#
# SMB.CONF(5)		The configuration file for the Samba suite 
#

<%
    import os
    from middlewared.utils import filter_list
    from middlewared.plugins.account import DEFAULT_HOME_PATH
    from middlewared.plugins.idmap_.utils import TRUENAS_IDMAP_MAX
    from middlewared.plugins.smb_.constants import LOGLEVEL_MAP, SMBPath
    from middlewared.plugins.directoryservices import DSStatus, SSL

    guest_enabled = any(filter_list(render_ctx['sharing.smb.query'], [['guestok', '=', True]]))
    fsrvp_enabled = any(filter_list(render_ctx['sharing.smb.query'], [['fsrvp', '=', True]]))

    ad_enabled = render_ctx['directoryservices.get_state']['activedirectory'] != 'DISABLED'
    if ad_enabled:
        ad_idmap = filter_list(
            render_ctx['idmap.query'],
            [('name', '=', 'DS_TYPE_ACTIVEDIRECTORY')],
            {'get': True}
        )
    else:
        ad_idmap = None

    home_share = filter_list(render_ctx['sharing.smb.query'], [['home', '=', True]])
    if home_share:
        if ad_enabled:
            home_path_suffix = '%D/%U'
        elif not home_share[0]['path_suffix']:
            home_path_suffix = '%U'
        else:
            home_path_suffix = home_share[0]['path_suffix']

        home_path = os.path.join(home_share[0]['path'], home_path_suffix)
    else:
        home_path = DEFAULT_HOME_PATH

    ldap_enabled = render_ctx['directoryservices.get_state']['ldap'] != 'DISABLED'
    loglevelint = int(LOGLEVEL_MAP.inv.get(render_ctx['smb.config']['loglevel'], 1))

    """
    First set up our legacy / default SMB parameters. Several are related to
    making sure that we don't have printing support enabled.

    fruit:nfs_aces
    fruit:zero_file_id
    ------------------
    are set to ensure that vfs_fruit will always have appropriate configuration.
    nfs_aces allows clients to chmod via special ACL entries. This reacts
    poorly with rich ACL models.
    vfs_fruit has option to set the file ID to zero, which causes client to
    fallback to algorithically generated file ids by hashing file name rather
    than using server-provided ones. This is not handled properly by all
    MacOS client versions and a hash collision can lead to data corruption.

    restrict anonymous
    ------------------
    We default to disabling anonymous IPC$ access. This is mostly in response
    to being flagged by security scanners. We have to re-enable if server guest
    access is enabled.

    winbind request timeout
    ------------------
    The nsswitch is only loaded once for the life of a running process on Linux
    and so winbind will always be present. In case of standalone server we want
    to reduce the risk that unhealthy winbind state would cause hangs in NSS
    for middlewared.

    passdb backend
    ------------------
    The passdb backend is stored in non-default path in order to prevent open
    handles from affecting system dataset operations. This is safe because we
    regenerate the passdb.tdb file on reboot.

    obey pam restrictions
    ------------------
    This is currently only required for case where user homes share is in use
    because we rely on pam_mkhomedir to auto-generate the path.

    It introduces a potential failure mode where pam_session() failure will
    lead to inability access SMB shares, and so at some point we should remove
    the pam_mkhomedir dependency.
    """
    smbconf = {
        'disable spoolss': True,
        'dns proxy': False,
        'load printers': False,
        'max log size': 5120,
        'printcap': '/dev/null',
        'bind interfaces only': True,
        'fruit:nfs_aces': False,
        'fruit:zero_file_id': False,
        'restrict anonymous': 0 if guest_enabled else 2,
        'winbind request timeout': 60 if ad_enabled else 2,
        'passdb backend': f'tdbsam:{SMBPath.PASSDB_DIR.value[0]}/passdb.tdb',
        'workgroup': render_ctx['smb.config']['workgroup'],
        'netbios name': render_ctx['smb.config']['netbiosname_local'],
        'netbios aliases': ' '.join(render_ctx['smb.config']['netbiosalias']),
        'guest account': render_ctx['smb.config']['guest'] if render_ctx['smb.config']['guest'] else 'nobody',
        'obey pam restrictions': any(home_share),
        'create mask': render_ctx['smb.config']['filemask'] or '0744',
        'directory mask': render_ctx['smb.config']['dirmask'] or '0755',
        'ntlm auth': render_ctx['smb.config']['ntlmv1_auth'],
        'server multichannel support': render_ctx['smb.config']['multichannel'],
        'unix charset': render_ctx['smb.config']['unixcharset'],
        'local master': render_ctx['smb.config']['localmaster'],
        'server string': render_ctx['smb.config']['description'],
        'log level': loglevelint,
        'logging': 'file',
        'registry shares': True,
        'include': 'registry',
    }

    """
    When guest access is enabled on _any_ SMB share we have to change the
    behavior of when the server maps to the guest account. `Bad User` here means
    that attempts to authenticate as a user that does not exist on the server
    will be automatically mapped to the guest account. This can lead to unexpected
    access denied errors, but many legacy users depend on this functionality and
    so we canot remove it.
    """
    if guest_enabled:
        smbconf['map to guest'] = 'Bad User'

    """
    If fsrvp is enabled on any share, then we need to have samba fork off an
    fssd daemon to handle snapshot management requests.
    """
    if fsrvp_enabled:
        smbconf.update({
            'rpc_daemon:fssd': 'fork',
            'fss:prune stale': True,
        })

    if render_ctx['smb.config']['enable_smb1']:
       smbconf['server min protocol'] = 'NT1'

    if render_ctx['smb.config']['syslog']:
       smbconf['logging'] = f'syslog@{min(3, loglevelint)} file'

    if smb_bindips := render_ctx['smb.config']['bindip']:
       allowed_ips = set(middleware.call_sync('smb.bindip_choices').values())
       if (rejected := set(smb_bindips) - allowed_ips):
           middleware.logger.warning(
               '%s: IP address(es) are no longer in use and should be removed '
               'from SMB configuration.', rejected
           )

       smbconf['interfaces'] = ' '.join(allowed_ips & set(smb_bindips))

    """
    The following LDAP parameters are defined for the purpose of configuring
    Samba as a legacy NT-style domain controller or backup domain controller
    with an OpenLDAP server acting as the passdb backend. This is scheduled
    for planned deprecation. FreeIPA-related SMB server parameters will go
    here once SSSD is merged.
    """
    if ldap_enabled:
        lc = middleware.call_sync('ldap.config')
        if lc['has_samba_schema']:
            # Legacy LDAP parameters
            smbconf.update({
                'server role': 'member server',
                'passdb backend': f'ldapsam:{" ".join(lc["uri_list"])}',
                'ldap admin dn': lc['binddn'],
                'ldap suffix': lc['basedn'],
                'ldap ssl': 'start tls' if lc['ssl'] == SSL.USESTARTTLS.value else 'off',
                'ldap passwd sync': 'Yes',
                'ldapsam:trusted': True,
                'local master': False,
                'domain master': False,
                'preferred master': False,
                'security': 'user',
            })
            if lc['kerberos_principal']:
                smbconf['kerberos method'] = 'system keytab'

    """
    The following are our default Active Directory related parameters

    winbindd max domain connections
    ------------------
    Winbindd defaults to a single connection per domain controller. Real
    life testing in enterprise environments indicated that this was
    often a bottleneck on busy servers. Ten has been default since FreeNAS
    11.2 and we have yet to see cases where it needs to scale higher.


    allow trusted domains
    ------------------
    We disable support for trusted domains by default due to need to configure
    idmap backends for them. There is separate validation when the field is
    enabled in the AD plugin to check that user has properly configured idmap
    settings. If idmap settings are not configured, then SID mappings are
    written to the default idmap backend (which is a TDB file on the system
    dataset). This is not desirable because the insertion for a domain is
    first-come-first-serve (not consistent between servers).


    winbind enum users
    winbind enum groups
    ------------------
    These are defaulted to being on to preserve legacy behavior and meet user
    expectations based on long histories of howto guides online. They affect
    whether AD users / groups will appear when full lists of users / groups
    via getpwent / getgrent. It does not impact getpwnam and getgrnam.
    """
    if ad_enabled:
        ac = middleware.call_sync('activedirectory.config')
        smbconf.update({
            'server role': 'member server',
            'kerberos method': 'secrets and keytab',
            'security': 'ADS',
            'local master': False,
            'domain master': False,
            'preferred master': False,
            'winbind cache time': 7200,
            'winbind max domain connections': 10,
            'winbind use default domain': ac['use_default_domain'],
            'client ldap sasl wrapping': 'seal',
            'template shell': '/bin/sh',
            'allow trusted domains': ac['allow_trusted_doms'],
            'realm': ac['domainname'],
            'ads dns update': False,
            'winbind nss info': ac['nss_info'].lower(),
            'template homedir': home_path,
            'winbind enum users': not ac['disable_freenas_cache'],
            'winbind enum groups': not ac['disable_freenas_cache'],
        })

    """
    The following part generates the smb.conf parameters from our idmap plugin
    settings. This is primarily relevant for case where TrueNAS is joined to
    an Active Directory domain.
    """
    for i in render_ctx['idmap.query']:
        match i['name']:
            case 'DS_TYPE_DEFAULT_DOMAIN':
                if ad_idmap and ad_idmap['idmap_backend'] == 'AUTORID':
                    continue

                domain = '*'
            case 'DS_TYPE_ACTIVEDIRECTORY':
                if not ad_enabled:
                    continue
                if i['idmap_backend'] == 'AUTORID':
                    domain = '*'
                else:
                    domain = render_ctx['smb.config']['workgroup']
            case 'DS_TYPE_LDAP':
                if not ldap_enabled or not lc['has_samba_schema']:
                    continue

                # Legacy LDAP-based domain. In this case we'll rely
                # LDAP nss plugin exclusively.
                domain = render_ctx['smb.config']['workgroup']
                idmap_prefix = f'idmap config {domain} :'
                smbconf.update({
                    f'{idmap_prefix} backend': 'nss',
                    f'{idmap_prefix} range': f'1000 - {TRUENAS_IDMAP_MAX}'
                })
                continue
            case _:
                domain = i['name']

        idmap_prefix = f'idmap config {domain} :'
        smbconf.update({
            f'{idmap_prefix} backend': i['idmap_backend'].lower(),
            f'{idmap_prefix} range': f'{i["range_low"]} - {i["range_high"]}',
        })

        disable_starttls = False
        for k, v in i['options'].items():
            backend_parameter = 'realm' if k == 'cn_realm' else k
            match k:
                case 'ldap_server':
                    value = 'ad' if v == 'AD' else 'stand-alone'
                case 'ldap_url':
                    value = f'{"ldaps://" if i["options"]["ssl"]  == "ON" else "ldap://"}{v}'
                case 'ssl':
                    if v != 'STARTTLS':
                        disable_startls = True
                    continue
                case _:
                    value = v

            smbconf.update({f'{idmap_prefix} {backend_parameter}': value})

%>\

[global]
% if render_ctx['failover.status'] in ('SINGLE', 'MASTER'):
% for param, value in smbconf.items():
    ${param} = ${value}
% endfor
% else:
    netbiosname = TN_STANDBY
% endif
