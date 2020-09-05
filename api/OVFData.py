#
#   OVF Data - Parses v2.0 OVF XML
#
#   OVFData.py - Modifications by Jani Tammi <jasata@utu.fi>
#   0.1.0   2019-12-26  Initial version.
#   0.1.1   2020-09-05  Header description added.
#
#
#   Create OVFData object with OVF XML string.
#   Read details from object attributes.
#
#     .name: str            Virtual machine name
#     .description: str     Virtual machine description
#     .osid: int            See _os_type in class OVFData
#     .ostype: str          See _os_type in class OVFData
#     .cpus: int            Number of CPUs
#     .ram: int             Amount of RAM in bytes
#     .disksize: int        Disk size in bytes
#
#   USAGE
#       ovf = OVFData(ovf_xml)
#       print(f"This VM has {ovf.ram} bytes of RAM")
#
import logging
import xml.etree.ElementTree as ET

class OVFData():
    """OVF data parser for OVF XML string."""
    _os_type = {
        '0': 'Unknown',
        '1': 'Other',
        '2': 'MACOS',
        '3': 'ATTUNIX',
        '4': 'DGUX',
        '5': 'DECNT',
        '6': 'Tru64 UNIX',
        '7': 'OpenVMS',
        '8': 'HPUX',
        '9': 'AIX',
        '10': 'MVS',
        '11': 'OS400',
        '12': 'OS/2',
        '13': 'JavaVM',
        '14': 'MSDOS',
        '15': 'WIN3x',
        '16': 'WIN95',
        '17': 'WIN98',
        '18': 'WINNT',
        '19': 'WINCE',
        '20': 'NCR3000',
        '21': 'NetWare',
        '22': 'OSF',
        '23': 'DC/OS',
        '24': 'Reliant UNIX',
        '25': 'SCO UnixWare',
        '26': 'SCO OpenServer',
        '27': 'Sequent',
        '28': 'IRIX',
        '29': 'Solaris',
        '30': 'SunOS',
        '31': 'U6000',
        '32': 'ASERIES',
        '33': 'HP NonStop OS',
        '34': 'HP NonStop OSS',
        '35': 'BS2000',
        '36': 'LINUX',
        '37': 'Lynx',
        '38': 'XENIX',
        '39': 'VM',
        '40': 'Interactive UNIX',
        '41': 'BSDUNIX',
        '42': 'FreeBSD',
        '43': 'NetBSD',
        '44': 'GNU Hurd',
        '45': 'OS9',
        '46': 'MACH Kernel',
        '47': 'Inferno',
        '48': 'QNX',
        '49': 'EPOC',
        '50': 'IxWorks',
        '51': 'VxWorks',
        '52': 'MiNT',
        '53': 'BeOS',
        '54': 'HP MPE',
        '55': 'NextStep',
        '56': 'PalmPilot',
        '57': 'Rhapsody',
        '58': 'Windows 2000',
        '59': 'Dedicated',
        '60': 'OS/390',
        '61': 'VSE',
        '62': 'TPF',
        '63': 'Windows (R) Me',
        '64': 'Caldera Open UNIX',
        '65': 'OpenBSD',
        '66': 'Not Applicable',
        '67': 'Windows XP',
        '68': 'z/OS',
        '69': 'Microsoft Windows Server 2003',
        '70': 'Microsoft Windows Server 2003 64-Bit',
        '71': 'Windows XP 64-Bit',
        '72': 'Windows XP Embedded',
        '73': 'Windows Vista',
        '74': 'Windows Vista 64-Bit',
        '75': 'Windows Embedded for Point of Service',
        '76': 'Microsoft Windows Server 2008',
        '77': 'Microsoft Windows Server 2008 64-Bit',
        '78': 'FreeBSD 64-Bit',
        '79': 'RedHat Enterprise Linux',
        '80': 'RedHat Enterprise Linux 64-Bit',
        '81': 'Solaris 64-Bit',
        '82': 'SUSE',
        '83': 'SUSE 64-Bit',
        '84': 'SLES',
        '85': 'SLES 64-Bit',
        '86': 'Novell OES',
        '87': 'Novell Linux Desktop',
        '88': 'Sun Java Desktop System',
        '89': 'Mandriva',
        '90': 'Mandriva 64-Bit',
        '91': 'TurboLinux',
        '92': 'TurboLinux 64-Bit',
        '93': 'Ubuntu',
        '94': 'Ubuntu 64-Bit',
        '95': 'Debian',
        '96': 'Debian 64-Bit',
        '97': 'Linux 2.4.x',
        '98': 'Linux 2.4.x 64-Bit',
        '99': 'Linux 2.6.x',
        '100': 'Linux 2.6.x 64-Bit',
        '101': 'Linux 64-Bit',
        '102': 'Other 64-Bit',
        '103': 'Microsoft Windows Server 2008 R2',
        '104': 'VMware ESXi',
        '105': 'Microsoft Windows 7',
        '106': 'CentOS 32-bit',
        '107': 'CentOS 64-bit',
        '108': 'Oracle Linux 32-bit',
        '109': 'Oracle Linux 64-bit',
        '110': 'eComStation 32-bitx',
        '111': 'Microsoft Windows Server 2011',
        '113': 'Microsoft Windows Server 2012',
        '114': 'Microsoft Windows 8',
        '115': 'Microsoft Windows 8 64-bit',
        '116': 'Microsoft Windows Server 2012 R2'
    }

    def __init__(self, xmlstring: str, logger = None):
        # Namespaces are listed in the <Envelope> tag attributes as xmlns:<ns>
        # TODO #1:  Read attribute ovf:version and require "2.0"
        # TODO #2:  Read namespaces from <Envelope> because what is hardcoded
        #           here, may or may not hold true for all .OVF files.
        self._ns = {
            'cim':  "http://schemas.dmtf.org/wbem/wscim/1/common",
            'ovf':  "http://schemas.dmtf.org/ovf/envelope/2",
            'rasd': "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/"
                    "CIM_ResourceAllocationSettingData",
            'sasd': "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/"
                    "CIM_StorageAllocationSettingData.xsd",
            'vmw':  "http://www.vmware.com/schema/ovf",
            'vssd': "http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/"
                    "CIM_VirtualSystemSettingData"
        }
        # NULL logger, if none provided
        if logger:
            self.logger = logger
        else:
            logging.getLogger('dummy').addHandler(logging.NullHandler())

        self._xmlstring         = xmlstring
        self._root              = None
        #
        # Public data
        #
        self.name: str          = None
        self.description: str   = None
        self.osid: int          = None
        self.ostype: str        = None
        self.cpus: int          = None
        self.ram: int           = None
        self.disksize: int      = None
        #
        # Try to make sense of the XML...
        #
        self._parse()
        #
        # Convert to int
        #
        if self.osid:
            self.osid = int(self.osid)
        if self.cpus:
            self.cpus = int(self.cpus)
        if self.ram:
            self.ram = int(self.ram) * (1024 * 1024)
        if self.disksize:
            self.disksize = int(self.disksize)



    def _parse(self):
        tree = ET.ElementTree(ET.fromstring(self._xmlstring))
        self._root = tree.getroot()
        self.logger.debug(
            f"root tag: '{self._root.tag}', attributes: '{self._root.attrib}'"
        )
        self._read_system_data()
        self._read_disk_data()



    def _nsattr(self, attr, ns=None):
        """Prefixes the attribute with namespace"""
        return f"{{{self._ns[ns]}}}{attr}" if ns else attr



    def _read_system_data(self):
        try:
            # <VirtualSystem ovf:id="DTEK2041">
            v_sys = self._root.find('ovf:VirtualSystem', self._ns)
            ### Name
            self.name = v_sys.get(self._nsattr('id', 'ovf'))
            ### Description
            annotation = v_sys.find(
                'ovf:AnnotationSection/ovf:Annotation',
                self._ns
            )
            if annotation:
                self.description = annotation.text
            #
            v_os = v_sys.find('ovf:OperatingSystemSection', self._ns)
            self.osid = v_os.get(self._nsattr('id', 'ovf'))
            # OS type -string from lookup dictionary
            self.ostype = self._os_type[self.osid]
            #
            v_cpu = v_sys.find(
                './ovf:VirtualHardwareSection/ovf:Item/[rasd:ResourceType="3"]',
                self._ns
            )
            # NOTE VMware has vmw:CoresPerSocket. Ignored #####################
            virtual_quantity = v_cpu.find('rasd:VirtualQuantity', self._ns)
            if virtual_quantity:
                self.cpus = virtual_quantity.text
            v_mem = v_sys.find(
                './ovf:VirtualHardwareSection/ovf:Item/[rasd:ResourceType="4"]',
                self._ns
            )
            ### RAM
            virtual_memory = v_mem.find('rasd:VirtualQuantity', self._ns)
            if virtual_memory:
                self.ram = virtual_memory .text
            self.logger.debug(
                f"'{self.name}' ({self.ostype}): "
                f"{self.cpus} CPUs, {self.ram} MB RAM"
            )
        except Exception as e:
            self.logger.exception("Error parsing system data")



    def _read_disk_data(self):
        try:
            file_refs = self._root.findall(
                './ovf:References/ovf:File',
                self._ns
            )
            files = dict()
            for ref in file_refs:
                files[ref.get(self._nsattr('id', 'ovf'))] = \
                    ref.get(self._nsattr('href', 'ovf'))
            self.logger.debug(f"References/File: {files}")
            diskrefs = self._root.findall(
                './ovf:DiskSection/ovf:Disk',
                self._ns
            )
            disks = dict()
            for ref in diskrefs:
                capacity = ref.get(self._nsattr('capacity', 'ovf'))
                fileref = ref.get(self._nsattr('fileRef', 'ovf'))
                diskid = f"ovf:/disk/{ref.get(self._nsattr('diskId', 'ovf'))}"
                # Add to disks, although, not used in this implementation
                disks[diskid] = {
                    'capacity': capacity,
                    'file': files[fileref]
                }
                # Add to total disk size
                self.disksize = int(capacity) + (self.disksize or 0)
            self.logger.debug(f"DiskSection/Disk: {disks}")
        except Exception as e:
            self.logger.exception("Error while reading disk data!")



    def __str__(self):
        """Useful for debugging and development purposes."""
        lw = 14 # label width
        string = ""
        for a in [a for a in dir(self) if not a.startswith('_') and not callable(getattr(self, a))]:
            string += f"{a: >{lw}} : {getattr(self, a)}\n"
        return string



# EOF
