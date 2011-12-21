#+
# Copyright 2010 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#####################################################################

from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings

from freenasUI import choices
from freenasUI.contrib.IPAddressField import IPAddressField
from freeadmin.models import Model, UserField, GroupField
from freenasUI.middleware.notifier import notifier
from freeadmin.models import PathField
from storage.models import Disk
import choices

class Settings(Model):
    stg_guiprotocol = models.CharField(
            max_length=120,
            choices=choices.PROTOCOL_CHOICES,
            default="http",
            verbose_name = _("Protocol")
            )
    stg_guiaddress = models.CharField(
            max_length=120,
            blank=True,
            default='0.0.0.0',
            verbose_name = _("WebGUI Address")
            )
    stg_guiport = models.CharField(
            max_length=120,
            blank=True,
            default='',
            verbose_name = _("WebGUI Port")
            )
    stg_language = models.CharField(
            max_length=120,
            choices=settings.LANGUAGES,
            default="en",
            verbose_name = _("Language")
            )
    stg_timezone = models.CharField(
            max_length=120,
            choices=choices.TimeZoneChoices(),
            default="America/Los_Angeles",
            verbose_name = _("Timezone")
            )
    stg_syslogserver = IPAddressField(
            default='',
            blank=True,
            verbose_name = _("Syslog server")
            )

    class Meta:
        verbose_name = _("Settings")

    class FreeAdmin:
        deletable = False

class NTPServer(Model):
    ntp_address = models.CharField(
            verbose_name=_("Address"),
            max_length=120,
            )
    ntp_burst = models.BooleanField(
            verbose_name=_("Burst"),
            default=False,
            help_text=_("When the server is reachable, send a burst of eight packets instead of the usual one. This is designed to improve timekeeping quality with the server command and s addresses."),
            )
    ntp_iburst = models.BooleanField(
            verbose_name=_("IBurst"),
            default=True,
            help_text=_("When the server is unreachable, send a burst of eight packets instead of the usual one. This is designed to speed the initial synchronization acquisition with the server command and s addresses."),
            )
    ntp_prefer = models.BooleanField(
            verbose_name=_("Prefer"),
            default=False,
            help_text=_("Marks the server as preferred. All other things being equal, this host will be chosen for synchronization among a set of correctly operating hosts."),
            )
    ntp_minpoll = models.IntegerField(
            verbose_name=_("Min. Poll"),
            default=6,
            validators=[MinValueValidator(4)],
            help_text=_("The minimum poll interval for NTP messages, as a power of 2 in seconds. Defaults to 6 (64 s), but can be decreased to a lower limit of 4 (16 s)"),
            )
    ntp_maxpoll = models.IntegerField(
            verbose_name=_("Max. Poll"),
            default=10,
            validators=[MaxValueValidator(17)],
            help_text=_("The maximum poll interval for NTP messages, as a power of 2 in seconds. Defaults to 10 (1,024 s), but can be increased to an upper limit of 17 (36.4 h)"),
            )

    def __unicode__(self):
        return self.ntp_address

    class Meta:
        verbose_name = _("NTP Server")
        verbose_name_plural = _("NTP Servers")

    class FreeAdmin:
        pass

class Advanced(Model):
    adv_consolemenu = models.BooleanField(
            verbose_name = _("Enable Console Menu"))
    adv_serialconsole = models.BooleanField(
            verbose_name = _("Use Serial Console"))
    adv_consolescreensaver = models.BooleanField(
            verbose_name = _("Enable screen saver"))
    adv_firmwarevc = models.BooleanField(
            verbose_name = _("Automatically Check for New Firmware"))
    adv_systembeep = models.BooleanField(
            verbose_name = _("Beep on boot"))
    adv_tuning = models.BooleanField(
            verbose_name = _("Enable Special System Tuning"))
    adv_powerdaemon = models.BooleanField(
            verbose_name = _("Enable powerd (Power Saving Daemon)"))
    adv_zeroconfbonjour = models.BooleanField(
            verbose_name = _("Enable Zeroconf/Bonjour"))
    adv_swapondrive = models.IntegerField(
            validators=[MinValueValidator(0)],
            verbose_name = _("Swap size on each drive in GiB, affects new disks only.  Setting this to 0 disables swap creation completely (STRONGLY DISCOURAGED)."),
            default=2)
    adv_consolemsg = models.BooleanField(
            verbose_name = _("Show console messages in the footer"),
            default=True)
    adv_traceback = models.BooleanField(
            verbose_name = _("Show tracebacks in case of fatal errors"),
            default=False)
    adv_advancedmode = models.BooleanField(
            verbose_name = _("Show advanced fields by default"),
            default=False)
    # TODO: need geom_eli in kernel
    #adv_encswap = models.BooleanField(
    #        verbose_name = _("Encrypt swap space"),
    #        default=False)
    adv_motd = models.TextField(
            max_length=1024,
            verbose_name = _("MOTD banner"),
            )

    class Meta:
        verbose_name = _("Advanced")

    class FreeAdmin:
        deletable = False

## System|Advanced|Email
class Email(Model):
    em_fromemail = models.CharField(
            max_length=120,
            verbose_name = _("From email"),
            help_text = _("An email address that the system will use for the sending address for mail it sends, eg: freenas@example.com"),
            blank=True
            )
    em_outgoingserver = models.CharField(
            max_length=120,
            verbose_name = _("Outgoing mail server"),
            help_text = _("A hostname or ip that will accept our mail, for instance mail.example.org, or 192.168.1.1"),
            blank=True
            )
    em_port = models.IntegerField(
            default=25,
            validators=[MinValueValidator(1), MaxValueValidator(65535)],
            help_text = _("An integer from 1 - 65535, generally will be 25, 465, or 587"),
            verbose_name = _("Port to connect to")
            )
    em_security = models.CharField(
            max_length=120,
            choices=choices.SMTPAUTH_CHOICES,
            default="plain",
            help_text = _("encryption of the connection"),
            verbose_name = _("TLS/SSL")
            )
    em_smtp = models.BooleanField(
            verbose_name = _("Use SMTP Authentication"),
            default=False
            )
    em_user = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Username"),
            help_text = _("A username to authenticate to the remote server"),
            )
    em_pass = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Password"),
            help_text = _("A password to authenticate to the remote server"),
            )
    class Meta:
        verbose_name = _("Email")

    class FreeAdmin:
        deletable = False

class SSL(Model):
    ssl_org = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Organization"),
            help_text = _("Organization Name (eg, company)"),
            )
    ssl_unit = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Organizational Unit"),
            help_text = _("Organizational Unit Name (eg, section)"),
            )
    ssl_email = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Email Address"),
            help_text = _("Email Address"),
            )
    ssl_city = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Locality"),
            help_text = _("Locality Name (eg, city)"),
            )
    ssl_state = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("State"),
            help_text = _("State or Province Name (full name)"),
            )
    ssl_country = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Country"),
            help_text = _("Country Name (2 letter code)"),
            )
    ssl_common = models.CharField(
            blank=True,
            null=True,
            max_length=120,
            verbose_name = _("Common Name"),
            help_text = _("Common Name (eg, YOUR name)"),
            )
    ssl_certfile = models.TextField(
            blank=True,
            null=True,
            verbose_name = _("SSL Certificate"),
            help_text = _("Cut and paste the contents of your private and public certificate files here."),
            )

    class Meta:
        verbose_name = _("SSL")

    class FreeAdmin:
        deletable = False

class CronJob(Model):
    cron_user = UserField(
            max_length=60,
            verbose_name=_("User"),
            help_text=_("The user to run the command")
            )
    cron_command = models.TextField(
            verbose_name=_("Command"),
            )
    cron_description = models.CharField(
            max_length=200,
            verbose_name=_("Description"),
            blank=True,
            )
    cron_minute = models.CharField(
            max_length=100,
            verbose_name=_("Minute"),
            help_text=_("Values 0-59 allowed."),
            )
    cron_hour = models.CharField(
            max_length=100,
            verbose_name=_("Hour"),
            help_text=_("Values 0-23 allowed."),
            )
    cron_daymonth = models.CharField(
            max_length=100,
            verbose_name=_("Day of month"),
            help_text=_("Values 1-31 allowed."),
            )
    cron_month = models.CharField(
            max_length=100,
            default='1,2,3,4,5,6,7,8,9,10,a,b,c',
            verbose_name=_("Month"),
            )
    cron_dayweek = models.CharField(
            max_length=100,
            default="1,2,3,4,5,6,7",
            verbose_name=_("Day of week"),
            )
    cron_enabled = models.BooleanField(
            default=True,
            verbose_name=_("Enabled"),
            )
    class Meta:
        verbose_name = _("Cron Job")
        verbose_name_plural = _("Cron Jobs")

    class FreeAdmin:
        icon_model = u"cronJobIcon"
        icon_object = u"cronJobIcon"
        icon_add = u"AddcronJobIcon"

    def __unicode__(self):
        return u"%d (%s)" % (self.id, self.cron_user)

    def get_human_minute(self):
        if self.cron_minute == '*':
            return _(u'Every minute')
        elif self.cron_minute.startswith('*/'):
            return _(u'Every %s minute(s)') % self.cron_minute.split('*/')[1]
        else:
            return self.cron_minute

    def get_human_hour(self):
        if self.cron_hour == '*':
            return _(u'Every hour')
        elif self.cron_hour.startswith('*/'):
            return _(u'Every %s hour(s)') % self.cron_hour.split('*/')[1]
        else:
            return self.cron_hour

    def get_human_daymonth(self):
        if self.cron_daymonth == '*':
            return _(u'Everyday')
        elif self.cron_daymonth.startswith('*/'):
            return _(u'Every %s days') % self.cron_daymonth.split('*/')[1]
        else:
            return self.cron_daymonth

    def get_human_month(self):
        months = self.cron_month.split(",")
        if len(months) == 12 or self.cron_month == '*':
            return _("Every month")
        mchoices = dict(choices.MONTHS_CHOICES)
        labels = []
        for m in months:
            if m in ('10', '11', '12'):
                m = chr(87 + int(m))
            labels.append(unicode(mchoices[m]))
        return ', '.join(labels)

    def get_human_dayweek(self):
        # TODO:
        # 1. Carve out the days input so that way one can say:
        #    Mon-Fri + Saturday -> Weekdays + Saturday.
        # 2. Get rid of the duplicate code.
        weeks = self.cron_dayweek.split(',')
        if len(weeks) == 7 or self.cron_dayweek == '*':
            return _('Everyday')
        if weeks == map(str, xrange(1, 6)):
            return _('Weekdays')
        if weeks == map(str, xrange(6, 8)):
            return _('Weekends')
        wchoices = dict(choices.WEEKDAYS_CHOICES)
        labels = []
        for w in weeks:
            labels.append(unicode(wchoices[str(w)]))
        return ', '.join(labels)

    def delete(self):
        super(CronJob, self).delete()
        try:
            notifier().restart("cron")
        except:
            pass

class Rsync(Model):
    rsync_path = PathField(
        verbose_name=_("Path"),
        abspath=False,
        )
    rsync_remotehost = models.CharField(
            max_length=120,
            verbose_name=_("Remote Host"),
            help_text=_("IP Address or hostname"),
            )
    rsync_mode = models.CharField(
            max_length=20,
            choices=choices.RSYNC_MODE_CHOICES,
            default='module',
            )
    rsync_remotemodule = models.CharField(
            max_length=120,
            verbose_name=_("Remote Module Name"),
            blank=True,
            help_text=_("Name of the module defined in the remote rsync daemon"),
            )
    rsync_remotepath = models.CharField(
            max_length=120,
            verbose_name=_("Remote Path"),
            blank=True,
            )
    rsync_direction = models.CharField(
            max_length=10,
            verbose_name=_("Direction"),
            help_text=_("Push - From local to remote machine. Pull - From remote to local machine."),
            default='push',
            choices=choices.RSYNC_DIRECTION,
            )
    rsync_desc = models.CharField(
            max_length=120,
            verbose_name=_("Short description"),
            blank=True,
            )
    rsync_minute = models.CharField(
            max_length=100,
            verbose_name=_("Minute"),
            help_text=_("Values 0-59 allowed."),
            )
    rsync_hour = models.CharField(
            max_length=100,
            verbose_name=_("Hour"),
            help_text=_("Values 0-23 allowed."),
            )
    rsync_daymonth = models.CharField(
            max_length=100,
            verbose_name=_("Day of month"),
            help_text=_("Values 1-31 allowed."),
            )
    rsync_month = models.CharField(
            max_length=100,
            default='1,2,3,4,5,6,7,8,9,10,a,b,c',
            verbose_name=_("Month"),
            )
    rsync_dayweek = models.CharField(
            max_length=100,
            default="1,2,3,4,5,6,7",
            verbose_name=_("Day of week"),
            )
    rsync_user = UserField(
            max_length=60,
            verbose_name=_("User"),
            help_text=_("The user to run the command"),
            )
    rsync_recursive = models.BooleanField(
            verbose_name=_("Recursive"),
            help_text=_("Recurse into directories"),
            default=True,
            )
    rsync_times = models.BooleanField(
            verbose_name=_("Times"),
            help_text=_("Preserve modification times"),
            default=True,
            )
    rsync_compress = models.BooleanField(
            verbose_name=_("Compress"),
            help_text=_("Compress data during the transfer"),
            default=True,
            )
    rsync_archive = models.BooleanField(
            verbose_name=_("Archive"),
            help_text=_("Archive mode"),
            default=False,
            )
    rsync_delete = models.BooleanField(
            verbose_name=_("Delete"),
            help_text=_("Delete files on the receiving side that don't exist on sender"),
            default=False,
            )
    rsync_quiet = models.BooleanField(
            verbose_name=_("Quiet"),
            help_text=_("Suppress non-error messages"),
            default=False,
            )
    rsync_preserveperm = models.BooleanField(
            verbose_name=_("Preserve permissions"),
            help_text=_("This option causes the receiving rsync to set the destination permissions to be the same as the source permissions"),
            default=False,
            )
    rsync_preserveattr = models.BooleanField(
            verbose_name=_("Preserve extended attributes"),
            help_text=_("This option causes rsync to update the remote extended attributes to be the same as the local ones"),
            default=False,
            )
    rsync_extra = models.CharField(
            max_length=120,
            verbose_name=_("Extra options"),
            help_text=_("Extra options to rsync command line (usually empty)"),
            blank=True
            )
    rsync_enabled = models.BooleanField(
            default=True,
            verbose_name=_("Enabled"),
            )
    class Meta:
        verbose_name = _("Rsync Task")
        verbose_name_plural = _("Rsync Tasks")

    class FreeAdmin:
        icon_model = u"rsyncIcon"
        icon_object = u"rsyncIcon"
        icon_add = u"AddrsyncTaskIcon"
        icon_view = u"ViewrsyncTaskIcon"

    def __unicode__(self):
        if self.rsync_desc:
            return self.rsync_desc
        return u"%d (%s)" % (self.id, self.rsync_user)

    def get_human_minute(self):
        if self.rsync_minute == '*':
            return _(u'Every minute')
        elif self.rsync_minute.startswith('*/'):
            return _(u'Every %s minute(s)') % self.rsync_minute.split('*/')[1]
        else:
            return self.rsync_minute

    def get_human_hour(self):
        if self.rsync_hour == '*':
            return _(u'Every hour')
        elif self.rsync_hour.startswith('*/'):
            return _(u'Every %s hour(s)') % self.rsync_hour.split('*/')[1]
        else:
            return self.rsync_hour

    def get_human_daymonth(self):
        if self.rsync_daymonth == '*':
            return _(u'Everyday')
        elif self.rsync_daymonth.startswith('*/'):
            return _(u'Every %s days') % self.rsync_daymonth.split('*/')[1]
        else:
            return self.rsync_daymonth

    def get_human_month(self):
        months = self.rsync_month.split(',')
        if len(months) == 12 or self.rsync_month == '*':
            return _("Every month")
        mchoices = dict(choices.MONTHS_CHOICES)
        labels = []
        for m in months:
            if m in ('10', '11', '12'):
                m = chr(87 + int(m))
            labels.append(unicode(mchoices[m]))
        return ', '.join(labels)

    def get_human_dayweek(self):
        weeks = self.rsync_dayweek.split(',')
        if len(weeks) == 7 or self.rsync_dayweek == '*':
            return _('Everyday')
        if weeks == map(str, xrange(1, 6)):
            return _('Weekdays')
        if weeks == map(str, xrange(6, 8)):
            return _('Weekends')
        wchoices = dict(choices.WEEKDAYS_CHOICES)
        labels = []
        for w in weeks:
            labels.append(unicode(wchoices[str(w)]))
        return ', '.join(labels)

    def delete(self):
        super(Rsync, self).delete()
        try:
            notifier().restart("cron")
        except:
            pass

class SMARTTest(Model):
    smarttest_disk = models.ForeignKey(
            Disk,
            limit_choices_to = {'disk_enabled': True},
            verbose_name=_("Disk"),
            )
    smarttest_type = models.CharField(
            choices=choices.SMART_TEST,
            max_length=2,
            verbose_name=_("Type"),
            blank=True,
            )
    smarttest_desc = models.CharField(
            max_length=120,
            verbose_name=_("Short description"),
            blank=True,
            )
    smarttest_hour = models.CharField(
            max_length=100,
            verbose_name=_("Hour"),
            help_text=_("Values 0-23 allowed."),
            )
    smarttest_daymonth = models.CharField(
            max_length=100,
            verbose_name=_("Day of month"),
            help_text=_("Values 1-31 allowed."),
            )
    smarttest_month = models.CharField(
            max_length=100,
            default='1,2,3,4,5,6,7,8,9,10,a,b,c',
            verbose_name=_("Month"),
            )
    smarttest_dayweek = models.CharField(
            max_length=100,
            default="1,2,3,4,5,6,7",
            verbose_name=_("Day of week"),
            )

    def get_human_hour(self):
        if self.smarttest_hour in ('..', '*'):
            return _(u'Every hour')
        elif self.smarttest_hour.startswith('*/'):
            return _(u'Every %s hour(s)') % self.smarttest_hour.split('*/')[1]
        else:
            return self.smarttest_hour

    def get_human_daymonth(self):
        if self.smarttest_daymonth in ('..', '*'):
            return _(u'Everyday')
        elif self.smarttest_daymonth.startswith('*/'):
            return _(u'Every %s days') % self.smarttest_daymonth.split('*/')[1]
        else:
            return self.smarttest_daymonth

    def get_human_month(self):
        months = self.smarttest_month.split(',')
        if len(months) == 12:
            return _("Every month")
        mchoices = dict(choices.MONTHS_CHOICES)
        labels = []
        for m in months:
            if m in ('10', '11', '12'):
                m = chr(87 + int(m))
            labels.append(unicode(mchoices[m]))
        return ', '.join(labels)

    def get_human_dayweek(self):
        weeks = self.smarttest_dayweek.split(',')
        if len(weeks) == 7:
            return _('Everyday')
        if weeks == map(str, xrange(1, 6)):
            return _('Weekdays')
        if weeks == map(str, xrange(6, 8)):
            return _('Weekends')
        wchoices = dict(choices.WEEKDAYS_CHOICES)
        labels = []
        for w in weeks:
            labels.append(unicode(wchoices[str(w)]))
        return ', '.join(labels)

    def __unicode__(self):
        return "%s (%s) " % (unicode(self.smarttest_disk), self.get_smarttest_type_display())

    def delete(self):
        super(SMARTTest, self).delete()
        try:
            notifier().restart("smartd")
        except:
            pass

    class Meta:
        verbose_name = _("S.M.A.R.T. Test")
        verbose_name_plural = _("S.M.A.R.T. Tests")
        unique_together = (
            ('smarttest_disk', 'smarttest_type'),
        )

    class FreeAdmin:
        icon_model = u"SMARTIcon"
        icon_object = u"SMARTIcon"
        icon_add = u"AddSMARTTestIcon"
        icon_view = u"ViewSMARTTestIcon"

class Sysctl(Model):
    sysctl_mib = models.CharField(
            max_length=50,
            unique=True,
            verbose_name=_("Variable"),
            )
    sysctl_value = models.CharField(
            max_length=50,
            verbose_name=_("Value"),
            )
    sysctl_comment = models.CharField(
            max_length=100,
            verbose_name=_("Comment"),
            blank=True,
            )

    def __unicode__(self):
        return unicode(self.sysctl_mib)

    def delete(self):
        super(Sysctl, self).delete()
        notifier().start("sysctl")

    class Meta:
        verbose_name = _("Sysctl")
        verbose_name_plural = _("Sysctls")

    class FreeAdmin:
        icon_model = u"SysctlIcon"
        icon_object = u"SysctlIcon"
        icon_add = u"AddSysctlIcon"
        icon_view = u"ViewSysctlIcon"

class Loader(Model):
    ldr_var = models.CharField(
            max_length=50,
            unique=True,
            verbose_name=_("Variable"),
            )
    ldr_value = models.CharField(
            max_length=50,
            verbose_name=_("Value"),
            )
    ldr_comment = models.CharField(
            max_length=100,
            verbose_name=_("Comment"),
            blank=True,
            )

    def __unicode__(self):
        return unicode(self.ldr_var)

    def delete(self):
        super(Loader, self).delete()
        notifier().start("loader")

    class Meta:
        verbose_name = _("Loader")
        verbose_name_plural = _("Loaders")

    class FreeAdmin:
        icon_model = u"LoaderIcon"
        icon_object = u"LoaderIcon"
        icon_add = u"AddLoaderIcon"
        icon_view = u"ViewLoaderIcon"
