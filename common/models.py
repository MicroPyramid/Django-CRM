from django.db import models
from datetime import datetime
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager

from common.utils import COUNTRIES, ROLES
import time


def img_url(self, filename):
    hash_ = int(time.time())
    return "%s/%s/%s" % ("profile_pics", hash_, filename)


class User(AbstractBaseUser, PermissionsMixin):
    file_prepend = "users/profile_pics"
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(('date joined'), auto_now_add=True)
    role = models.CharField(max_length=50, choices=ROLES)
    profile_pic = models.FileField(max_length=1000, upload_to=img_url, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    objects = UserManager()

    def get_short_name(self):
        return self.username

    def __unicode__(self):
        return self.email

    class Meta:
        ordering = ['-is_active']


class Address(models.Model):
    address_line = models.CharField(_("Address"), max_length=255, blank=True, null=True)
    street = models.CharField(_("Street"), max_length=55, blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State"), max_length=255, blank=True, null=True)
    postcode = models.CharField(_("Post/Zip-code"), max_length=64, blank=True, null=True)
    country = models.CharField(max_length=3, choices=COUNTRIES, blank=True, null=True)

    def __str__(self):
        return self.city if self.city else ""

    def get_complete_address(self):
        address = ""
        if self.address_line:
            address += self.address_line
        if self.street:
            if address:
                address += ", " + self.street
            else:
                address += self.street
        if self.city:
            if address:
                address += ", " + self.city
            else:
                address += self.city
        if self.state:
            if address:
                address += ", " + self.state
            else:
                address += self.state
        if self.postcode:
            if address:
                address += ", " + self.postcode
            else:
                address += self.postcode
        if self.country:
            if address:
                address += ", " + self.get_country_display()
            else:
                address += self.get_country_display()
        return address


class Team(models.Model):
    name = models.CharField(max_length=55)
    members = models.ManyToManyField(User)

    def __str__(self):
        return self.name


class Comment(models.Model):
    case = models.ForeignKey('cases.Case', blank=True, null=True, related_name="cases", on_delete=models.CASCADE)
    comment = models.CharField(max_length=255)
    commented_on = models.DateTimeField(auto_now_add=True)
    commented_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    account = models.ForeignKey(
        'accounts.Account', blank=True, null=True, related_name="accounts_comments", on_delete=models.CASCADE)
    lead = models.ForeignKey('leads.Lead', blank=True, null=True, related_name="leads", on_delete=models.CASCADE)
    opportunity = models.ForeignKey(
        'opportunity.Opportunity', blank=True, null=True, related_name="opportunity_comments", on_delete=models.CASCADE)
    contact = models.ForeignKey(
        'contacts.Contact', blank=True, null=True, related_name="contact_comments", on_delete=models.CASCADE)

    def get_files(self):
        return Comment_Files.objects.filter(comment_id=self)


class Comment_Files(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    updated_on = models.DateTimeField(auto_now_add=True)
    comment_file = models.FileField("File", upload_to="comment_files", default='')

    def get_file_name(self):
        if self.comment_file:
            return self.comment_file.path.split('/')[-1]
        else:
            return None


class Attachments(models.Model):
    created_by = models.ForeignKey(User, related_name='attachment_created_by', on_delete=models.CASCADE)
    file_name = models.CharField(max_length=60)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)
    attachment = models.FileField(max_length=1001, upload_to='attachments/%Y/%m/')
    lead = models.ForeignKey('leads.Lead', null=True, blank=True, related_name='lead_attachment', on_delete=models.CASCADE)
    account = models.ForeignKey('accounts.Account', null=True, blank=True, related_name='account_attachment', on_delete=models.CASCADE)
    contact = models.ForeignKey('contacts.Contact', on_delete=models.CASCADE, related_name='contact_attachment', blank=True, null=True)
    opportunity = models.ForeignKey('opportunity.Opportunity',blank=True,null=True,on_delete=models.CASCADE,related_name='opportunity_attachment')
    case = models.ForeignKey('cases.Case',blank=True,null=True,on_delete=models.CASCADE,related_name='case_attachment')


def document_path(self, filename):
    hash_ = int(time.time())
    return "%s/%s/%s" % ("docs", hash_, filename)

class Document(models.Model):
    title = models.CharField(max_length=1000, blank=True, null=True)
    document_file = models.FileField(upload_to=document_path, max_length=5000)
    created_by = models.ForeignKey(User, related_name='document_uploaded', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

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
                return ("audio", "fa fa-file-audio")
            elif self.is_document_file_video(ext):
                return ("video", "fa fa-file-video")
            elif self.is_document_file_image(ext):
                return ("image", "fa fa-file-image")
            elif self.is_document_file_pdf(ext):
                return ("pdf", "fa fa-file-pdf")
            elif self.is_document_file_code(ext):
                return ("code", "fa fa-file-code")
            elif self.is_document_file_text(ext):
                return ("text", "fa fa-file-alt")
            elif self.is_document_file_sheet(ext):
                return ("sheet", "fa fa-file-excel")
            elif self.is_document_file_zip(ext):
                return ("zip", "fa fa-file-archive")
            return ("file", "fa fa-file")
        return ("file", "fa fa-file")

    
    def __str__(self):
        return self.title