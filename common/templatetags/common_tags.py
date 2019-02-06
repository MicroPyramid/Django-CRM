from django import template
register = template.Library()


def is_document_file_image(ext):
    image_ext_list = ['bmp', 'dds', 'gif', 'jpg', 'jpeg', 'png', 'psd', 'pspimage',
                      'tga', 'thm', 'tif', 'tiff', 'yuv']
    return ext.lower() in image_ext_list

def is_document_file_audio(ext):
    audio_ext_list = ['aif', 'iff', 'm3u', 'm4a', 'mid', 'mp3',
                      'mpa', 'wav', 'wma']
    return ext.lower() in audio_ext_list

def is_document_file_video(ext):
    video_ext_list = ['3g2', '3gp', 'asf', 'avi', 'flv', 'm4v', 'mov',
                      'mp4', 'mpg', 'rm', 'srt', 'swf', 'vob', 'wmv']
    return ext.lower() in video_ext_list

def is_document_file_pdf(ext):
    pdf_ext_list = ['indd', 'pct', 'pdf']
    return ext.lower() in pdf_ext_list

def is_document_file_code(ext):
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

def is_document_file_text(ext):
    text_ext_list = ['doc', 'docx', 'log', 'msg', 'odt', 'pages', 'rtf',
                     'tex', 'txt', 'wpd', 'wps']
    return ext.lower() in text_ext_list

def is_document_file_sheet(ext):
    sheet_ext_list = ['csv', 'xls', 'xlsx',
                      'xlsm', 'xlsb', 'xltx', 'xltm', 'xlt']
    return ext.lower() in sheet_ext_list

def is_document_file_zip(ext):
    ext_list = ['zip', '7Z', 'gz', 'rar', 'ZIPX', 'ACE', 'tar', ]
    return ext.lower() in ext_list


@register.filter
def subtract(value, arg):
    return value - int(arg)
