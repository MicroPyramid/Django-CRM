from datetime import datetime
from django.db import models
# from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
# from django.db.models import Sum
# from django.template.defaultfilters import slugify


class Tag(models.Model):
    name = models.CharField(max_length=500)
    color = models.CharField(max_length=20, default="#999999", verbose_name=_("color"))
    created_by = models.ForeignKey(User, related_name="marketing_tags", null=True, on_delete=models.SET_NULL)

    @property
    def created_by_user(self):
        return self.created_by.serialized_data() if self.created_by else None


def attachment_url(self, filename):
    file_extension = filename.split('.')[-1]
    return "%s/Documents/%s" % (
        self.company, "attachment_" + str(slugify(datetime.now())) + "." + file_extension)
    # file_split = filename.split('.')
    # file_extension = file_split[-1]
    # path = "%s_%s_%s" % (file_split[0], self.profile.user.email, str(datetime.now()))
    # return str(self.company.subdomain) + "/users/" + str(self.profile.user.email) + \
    #     "/docs/" + slugify(path) + "." + file_extension


class Document(models.Model):
    title = models.CharField(max_length=155)
    description = models.CharField(max_length=2500, blank=True, null=True)
    document_file = models.FileField(upload_to=attachment_url)
    created_by = models.ForeignKey(User, related_name="created_marketing_documents", null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def is_document_file_image(self, ext):
        image_ext_list = ['bmp', 'dds', 'gif', 'jpg', 'jpeg', 'png', 'psd', 'pspimage',
                          'tga', 'thm', 'tif', 'tiff', 'yuv']
        return ext.lower() in image_ext_list

    def is_document_file_audio(self, ext):
        audio_ext_list = ['aif', 'iff', 'm3u', 'm4a', 'mid', 'mp3',
                          'mpa', 'wav', 'wma']
        return ext.lower() in audio_ext_list

    def is_document_file_video(self, ext):
        video_ext_list = ['3g2', '3gp', 'asf', 'avi', 'flv', 'm4v', 'mov',
                          'mp4', 'mpg', 'rm', 'srt', 'swf', 'vob', 'wmv']
        return ext.lower() in video_ext_list

    def is_document_file_pdf(self, ext):
        pdf_ext_list = ['indd', 'pct', 'pdf']
        return ext.lower() in pdf_ext_list

    def is_document_file_code(self, ext):
        code_ext_list = ['aspx', 'json', 'jsp', 'do', 'htm', 'html', 'ser',
                         'php', 'jad', 'cfm', 'xml', 'js', 'pod', 'asp',
                         'atomsvc', 'rdf', 'pou', 'jsf', 'abs', 'pl', 'asm',
                         'srz', 'luac', 'cod', 'lib', 'arxml', 'bas', 'ejs',
                         'fs', 'hbs', 's', 'ss', 'cms', 'pyc', 'vcxproj',
                         'jse', 'smali', 'xla', 'lxk', 'pdb', 'src', 'cs',
                         'ipb', 'ave', 'mst', 'vls', 'rcc', 'sax', 'scr',
                         'dtd', 'axd', 'mrl', 'xsl', 'ino', 'spr', 'xsd',
                         'cgi', 'isa', 'ws', 'rss', 'dvb', 'nupkg', 'xlm',
                         'v4e', 'rss', 'prg', 'form', 'bat', 'mrc', 'asi',
                         'jdp', 'fmb', 'graphml', 'gcode', 'aia', 'py', 'atp',
                         'mzp', 'o', 'scs', 'mm', 'cpp', 'java', 'gypi', 'idb',
                         'txml', 'c', 'vip', 'tra', 'rc', 'action', 'vlx',
                         'asta', 'pyo', 'lua', 'gml', 'prl', 'rfs', 'cpb',
                         'sh', 'rbf', 'gp', 'phtml', 'bp', 'scb', 'sln', 'vbp',
                         'wbf', 'bdt', 'mac', 'rpy', 'eaf', 'mc', 'mwp', 'gnt',
                         'h', 'swift', 'e', 'styl', 'cxx', 'as', 'liquid',
                         'dep', 'fas', 'vbs', 'aps', 'vbe', 'lss', 'cmake',
                         'resx', 'csb', 'dpk', 'pdml', 'txx', 'dbg', 'jsa',
                         'sxs', 'sasf', 'pm', 'csx', 'r', 'wml', 'au3', 'stm',
                         'cls', 'cc', 'ins', 'jsc', 'dwp', 'rpg', 'arb', 'bml',
                         'inc', 'eld', 'sct', 'sm', 'wbt', 'csproj', 'tcz',
                         'html5', 'gbl', 'cmd', 'dlg', 'tpl', 'rbt', 'xcp',
                         'tpm', 'qry', 'mfa', 'ptx', 'lsp', 'pag', 'ebc',
                         'php3', 'cob', 'csc', 'pyt', 'dwt', 'rb', 'wsdl',
                         'lap', 'textile', 'sfx', 'x', 'a5r', 'dbp', 'pmp',
                         'ipr', 'fwx', 'pbl', 'vbw', 'phl', 'cbl', 'pas',
                         'mom', 'dbmdl', 'lol', 'wdl', 'ppam', 'plx', 'vb',
                         'cgx', 'lst', 'lmp', 'vd', 'bcp', 'thtml', 'scpt',
                         'isu', 'mrd', 'perl', 'dtx', 'f', 'wpk', 'ipf', 'ptl',
                         'luca', 'hx', 'uvproj', 'qvs', 'vba', 'xjb',
                         'appxupload', 'ti', 'svn-base', 'bsc', 'mak',
                         'vcproj', 'dsd', 'ksh', 'pyw', 'bxml', 'mo', 'irc',
                         'gcl', 'dbml', 'mlv', 'wsf', 'tcl', 'dqy', 'ssi',
                         'pbxproj', 'bal', 'trt', 'sal', 'hkp', 'vbi', 'dob',
                         'htc', 'p', 'ats', 'seam', 'loc', 'pli', 'rptproj',
                         'pxml', 'pkb', 'dpr', 'scss', 'dsb', 'bb', 'vbproj',
                         'ash', 'rml', 'nbk', 'nvi', 'lmv', 'mw', 'jl', 'dso',
                         'cba', 'jks', 'ary', 'run', 'vps', 'clm', 'brml',
                         'msha', 'mdp', 'tmh', 'rdf', 'jsx', 'sdl', 'ptxml',
                         'fxl', 'wmw', 'dcr', 'bcc', 'cbp', 'bmo', 'bsv',
                         'less', 'gss', 'ctl', 'rpyc', 'ascx', 'odc', 'wiki',
                         'obr', 'l', 'axs', 'bpr', 'ppa', 'rpo', 'sqlproj',
                         'smm', 'dsr', 'arq', 'din', 'jml', 'jsonp', 'ml',
                         'rc2', 'myapp', 'cla', 'xme', 'obj', 'jsdtscope',
                         'gyp', 'datasource', 'cp', 'rh', 'lpx', 'a2w', 'ctp',
                         'ulp', 'nt', 'script', 'bxl', 'gs', 'xslt', 'mg',
                         'pch', 'mhl', 'zpd', 'psm1', 'asz', 'm', 'jacl',
                         'pym', 'rws', 'acu', 'ssq', 'wxs', 'coffee', 'ncb',
                         'akt', 'pyx', 'zero', 'hs', 'mkb', 'tru', 'xul',
                         'mfl', 'sca', 'sbr', 'master', 'opv', 'matlab',
                         'sami', 'agc', 'slim', 'tea', 'pbl', 'm51', 'mec',
                         'asc', 'gch', 'enml', 'ino', 'kst', 'jade', 'dfb',
                         'ips', 'rgs', 'vbx', 'cspkg', 'ncx', 'brs', 'wfs',
                         'ifp', 'nse', 'xtx', 'j', 'cx', 'ps1', 'nas', 'mk',
                         'ccs', 'vrp', 'lnp', 'cml', 'c#', 'idl', 'exp', 'apb',
                         'nsi', 'asmx', 'tdo', 'pjt', 'fdt', 's5d', 'mvba',
                         'mf', 'odl', 'bzs', 'jardesc', 'tgml', 'moc', 'wxi',
                         'cpz', 'fsx', 'jav', 'ocb', 'agi', 'tec', 'txl',
                         'amw', 'mscr', 'dfd', 'dpd', 'pun', 'f95', 'vdproj',
                         'xsc', 'diff', 'wxl', 'dgml', 'airi', 'kmt', 'ksc',
                         'io', 'rbw', 'sas', 'vcp', 'resources', 'param',
                         'cg', 'hlsl', 'vssscc', 'bgm', 'xn', 'targets', 'sl',
                         'gsc', 'qs', 'owl', 'devpak', 'phps', 'hdf', 'pri',
                         'nbin', 'xaml', 's4e', 'scm', 'tk', 'poc', 'uix',
                         'clw', 'factorypath', 's43', 'awd', 'htr', 'php2',
                         'classpath', 'pickle', 'rob', 'msil', 'ebx', 'tsq',
                         'lml', 'f90', 'lds', 'vup', 'pbi', 'swt', 'vap', 'ig',
                         'pdo', 'frt', 'fcg', 'c++', 'xcl', 'dfn', 'aar',
                         'for', 're', 'twig', 'ebm', 'dhtml', 'hc', 'pro',
                         'ahk', 'rule', 'bsh', 'jcs', 'zrx', 'wsdd', 'csp',
                         'drc', 'appxsym']
        return ext.lower() in code_ext_list

    def is_document_file_text(self, ext):
        text_ext_list = ['doc', 'docx', 'log', 'msg', 'odt', 'pages', 'rtf',
                         'tex', 'txt', 'wpd', 'wps']
        return ext.lower() in text_ext_list

    def is_document_file_sheet(self, ext):
        sheet_ext_list = ['csv', 'xls', 'xlsx',
                          'xlsm', 'xlsb', 'xltx', 'xltm', 'xlt']
        return ext.lower() in sheet_ext_list

    def is_document_file_zip(self, ext):
        ext_list = ['zip', '7Z', 'gz', 'rar', 'ZIPX', 'ACE', 'tar', ]
        return ext.lower() in ext_list

    def file_type(self):
        name_ext_list = self.document_file.url.split(".")
        if (len(name_ext_list) > 1):
            ext = name_ext_list[int(len(name_ext_list) - 1)]
            if self.is_document_file_audio(ext):
                return ("audio", "fa fa-file-audio-o")
            elif self.is_document_file_video(ext):
                return ("video", "fa fa-file-video-o")
            elif self.is_document_file_image(ext):
                return ("image", "fa fa-file-image-o")
            elif self.is_document_file_pdf(ext):
                return ("pdf", "fa fa-file-pdf-o")
            elif self.is_document_file_code(ext):
                return ("code", "fa fa-file-code-o")
            elif self.is_document_file_text(ext):
                return ("text", "fa fa-file-text")
            elif self.is_document_file_sheet(ext):
                return ("sheet", "fa fa-file-excel-o")
            elif self.is_document_file_zip(ext):
                return ("zip", "fa fa-file-archive-o")
            return ("file", "fa fa-file-o")
        return ("file", "fa fa-file-o")

    @property
    def file_type_code(self):
        return self.file_type()

    @property
    def document_file_path(self):
        return self.document_file.url if self.document_file else None

    @property
    def document_file_name(self):
        return self.document_file.name if self.document_file else None


class EmailTemplate(models.Model):
    created_by = models.ForeignKey(User, related_name="marketing_emailtemplates", null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=5000)
    subject = models.CharField(max_length=5000)
    html = models.TextField()

    class Meta:
        unique_together = (("title", "company"),)

    @property
    def created_by_user(self):
        return self.created_by.serialized_data() if self.created_by else None


class ContactList(models.Model):
    created_by = models.ForeignKey(User, related_name="marketing_contactlist", null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=500)
    tags = models.ManyToManyField(Tag)
    is_public = models.BooleanField(default=False)

    class Meta:
        unique_together = (("name", "company"),)

    @property
    def created_by_user(self):
        return self.created_by.serialized_data() if self.created_by else None

    @property
    def created_by_user_profile(self):
        if self.created_by is not None:
            profile = Profile.objects.filter(
                user=self.created_by, company=self.company).last()
            if profile is not None:
                return Skinner().parse(profile, fields=[
                    'employee_name', 'userid', 'profile_pic_path', 'employee_id'])
            else:
                return self.created_by.serialized_data()
        else:
            return None

    @property
    def created_on_format(self):
        return self.created_on.strftime('%b %d, %Y %I:%M %p')

    @property
    def created_on_since(self):
        return created_since(self.created_on)

    @property
    def created_by_company(self):
        return self.company.serialized_data() if self.company else None

    @property
    def tags_data(self):
        return Skinner().parse(
            self.tags.all(), fields=["id", "name", "color"])['data']

    @property
    def no_of_contacts(self):
        return self.contacts.all().count()

    @property
    def no_of_campaigns(self):
        return self.campaigns.all().count()

    @property
    def unsubscribe_contacts(self):
        return self.contacts.filter(is_unsubscribed=True).count()

    @property
    def bounced_contacts(self):
        return self.contacts.filter(is_bounced=True).count()

    @property
    def no_of_clicks(self):
        clicks = CampaignLog.objects.filter(
            contact__contact_list__in=[self]).aggregate(Sum('no_of_clicks'))['no_of_clicks__sum']
        return clicks


class Contact(models.Model):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 20 digits allowed."
    )
    created_by = models.ForeignKey(User, related_name="marketing_contacts_created_by", null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    contact_list = models.ManyToManyField(ContactList, related_name="contacts")
    name = models.CharField(max_length=500)
    email = models.EmailField()
    contact_number = models.CharField(validators=[phone_regex], max_length=20, blank=True, null=True)
    is_unsubscribed = models.BooleanField(default=False)
    is_bounced = models.BooleanField(default=False)
    company_name = models.CharField(max_length=500, null=True, blank=True)
    last_name = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=500, null=True, blank=True)
    state = models.CharField(max_length=500, null=True, blank=True)
    contry = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        unique_together = (("company", "email"),)


class Campaign(models.Model):
    STATUS_CHOICES = (
        ('Scheduled', 'Scheduled'),
        ('Cancelled', 'Cancelled'),
        ('Sending', 'Sending'),
        ('Preparing', 'Preparing'),
        ('Sent', 'Sent'),
    )

    title = models.CharField(max_length=5000)
    created_by = models.ForeignKey(User, related_name="marketing_campaigns_created_by", null=True, on_delete=models.SET_NULL)
    created_on = models.DateTimeField(auto_now_add=True)
    contact_lists = models.ManyToManyField(ContactList, related_name="campaigns")
    email_template = models.ForeignKey(EmailTemplate, blank=True, null=True, on_delete=models.SET_NULL)
    schedule_date_time = models.DateTimeField(blank=True, null=True)
    reply_to_email = models.EmailField(blank=True, null=True)
    subject = models.CharField(max_length=5000)
    html = models.TextField()
    html_processed = models.TextField(default="", blank=True)
    from_email = models.EmailField(blank=True, null=True)
    from_name = models.EmailField(blank=True, null=True)
    sent = models.IntegerField(default='0', blank=True)
    opens = models.IntegerField(default='0', blank=True)
    opens_unique = models.IntegerField(default='0', blank=True)
    bounced = models.IntegerField(default='0')
    status = models.CharField(default="Preparing", choices=STATUS_CHOICES, max_length=20)

    @property
    def no_of_unsubscribers(self):
        unsubscribers = self.campaign_contacts.filter(contact__is_unsubscribed=True).count()
        return unsubscribers


class Link(models.Model):
    campaign = models.ForeignKey(Campaign, related_name="marketing_links", on_delete=models.CASCADE)
    original = models.URLField(max_length=2100)
    clicks = models.IntegerField(default='0')
    unique = models.IntegerField(default='0')


class CampaignLog(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    campaign = models.ForeignKey(Campaign, related_name='campaign_contacts', on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, related_name="marketing_campaign_logs", null=True, on_delete=models.SET_NULL)
    message_id = models.CharField(max_length=1000, null=True, blank=True)


class CampaignLinkClick(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    link = models.ForeignKey(Link, blank=True, null=True, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    created_on = models.DateTimeField(auto_now_add=True)
    user_agent = models.CharField(max_length=2000, blank=True, null=True)
    contact = models.ForeignKey(Contact, blank=True, null=True, on_delete=models.CASCADE)


class CampaignOpen(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    created_on = models.DateTimeField(auto_now_add=True)
    user_agent = models.CharField(max_length=2000, blank=True, null=True)
    contact = models.ForeignKey(Contact, blank=True, null=True, on_delete=models.CASCADE)
