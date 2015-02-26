import binascii
import struct
import array
import sys
from hurry.filesize import size

part_types = {"00": "Unkown or Empty",
              "01": "12-bit FAT",
              "04": "16-bit FAT (< 32MB)",
              "05": "Extended MS-DOS Partition",
              "06": "FAT-16 (32MB to 2GB)",
              "07": "NTFS",
              "0B": "FAT-32 (CHS)",
              "0C": "FAT-32 (LBA)",
              "0E": "FAT-16 (LBA)"}

SECTOR_SIZE = 512

class DiskAnalyser():

    def __init__(self, filepath):
        self.filepath = filepath


    def read_disk_info(self, address,
                       reading_partition=True,
                       reading_volume=False):

        disk_info = []
        seek_address = int(address)
        read_range = 0

        if reading_partition:
            # if reading a partition just seek to address.
            seek_address = address
            read_range = 1
        else:
            # if reading volume info multiply address by sector size
            seek_address = address * SECTOR_SIZE
            read_range = 2


        with open(self.filepath, "rb") as f:

            # seek to sector address
            f.seek(seek_address)

            for i in xrange(read_range):
                part = ""
                for x in xrange(1, 17):
                    byte = f.read(1)
                    part = part + str(binascii.hexlify(byte).upper())

                disk_info.append(part)

        return disk_info



    def read_disk(self):
        """ Read 16 byte partition information from disk """

        with open(self.filepath, "rb") as f:
            # first partition is at 0x1BE, convert this to decimal value
            # seek that amount into the file, read the 16 bytes
            # and that is the MBR record for the partition
            # 0x1CE -> 446 - 1st partition
            # 0x1BE -> 462 - 2nd partition
            # 0x1DE -> 478 - 3rd partition
            # 0x1FE -> 494 - 4th partition
            partitions = [446, 462, 478, 494]
            part_info = []

            for partition in partitions:
                part = ""
                f.seek(partition)

                for x in xrange(1, 17):
                    byte = f.read(1)
                    part = part + str(binascii.hexlify(byte).upper())

                part_info.append(part)

        return part_info

    def toBigEndian(self, hexString):
        """ Convert hexString to Big-Endian Format """
        swappedBytes = ""
        chunk = ""
        lastpos = 0
        for c in xrange(0, len(hexString) + 2, 2):
            chunk = hexString[lastpos:c]
            swappedBytes = chunk + swappedBytes
            lastpos = c
        return swappedBytes

    def get_partition_type(self, p_type):
        """ Return partition type """
        for t in part_types:
            if t in part_types.keys():
                return part_types[p_type]

    def get_partition_info(self, partition_info):
        """ Pick out relavant partition information """

        j = 1
        p_info = []
        p_flag = ""
        p_type = ""
        p_start_addr = ""
        p_size = ""

        for i in partition_info:
            p_flag = self.toBigEndian(i[:2] + '0x')
            p_type = self.toBigEndian(i[8:10] + '0x') + "(" + self.get_partition_type(i[8:10]) + ")"
            p_start_addr = self.toBigEndian(i[16:24] + '0x') + " (" + str(int(self.toBigEndian(i[16:24]), 16)) + ") "
            p_size = self.toBigEndian(i[24:34] + '0x') + " (" + str(int(self.toBigEndian(i[24:34]), 16)) + ")"

            p_info.append({"Partition #": j,
                           "Flag": p_flag,
                           "Type": p_type,
                           "Sector Start Address": p_start_addr,
                           "Partition Size": p_size
                       })
            j += 1

        return p_info

    def get_partition_information(self):
        part_info = self.read_disk()
        partition_info = self.get_partition_info(part_info)

        return partition_info

    def get_volume_info(self, address):

        # take address in deciaml
        res_area_sector = int(address[12:14])

        # create address of sector we need to seek to
        sector_address = res_area_sector * SECTOR_SIZE

        vol_info = []

        with open(self.filepath, "rb") as f:
            f.seek(sector_address)
            for i in xrange(2):
                part = ""
                for x in xrange(1, 17):
                    byte = f.read(1)
                    part = part + str(binascii.hexlify(byte).upper())

                vol_info.append(part)

        print vol_info

        # Reserved Area size in Sectors
        # 0Eh - 2 bytes
        reserved_area_size = int(self.toBigEndian(vol_info[0][-4:]), 16)

        # FAT size in Sectors
        # 16h, 17h  - 1 word
        fat_size = int(self.toBigEndian(vol_info[1][12:16]), 16)

        # No. of FATs
        # 10h - 1 byte
        num_fats = int(self.toBigEndian(vol_info[1][:2]), 16)

        # FAT Area = (No. of FATs * FAT size in secors)
        fat_area_size =  fat_size * num_fats

        # print
        # print reserved_area_size
        # print fat_size
        # print num_fats
        # print fat_area_size

        # No. of root dir entries
        # 11h - 1 word
        num_root_dirs = int(self.toBigEndian(vol_info[1][2:6]),16)

        # always 32 bytes for a FAT volume
        dir_entry_size = 32

        # Root dir size in sectors
        root_dir_size = (num_root_dirs * dir_entry_size) / SECTOR_SIZE

        # No. of sectors per cluster
        # 0D - 1 byte
        num_sectors = int(self.toBigEndian(vol_info[0][-6: -4]),16)

        # print
        # print num_root_dirs
        # print root_dir_size
        # print num_sectors

        DA_address = res_area_sector + reserved_area_size + fat_area_size
        cluster_2_addr = DA_address + root_dir_size

        # print
        # print DA_address
        # print cluster_2_addr

        print "First sector of Disk:", 0
        print "First sector of Reserved Area:", res_area_sector
        print "First sector of FAT Area:", res_area_sector + reserved_area_size
        print "First sector of Data Area:", DA_address
        print "Cluster #2 location:", cluster_2_addr, "(" + str(cluster_2_addr), "to", str(cluster_2_addr + num_sectors) + ")"
        # print hex(DA_address*512)

        return {"First sector of Disk": 0,
                "First sector of Reserved Area": res_area_sector,
                "First sector of FAT Area": res_area_sector + reserved_area_size,
                "First sector of Data Area": DA_address,
                "Cluster #2 location": cluster_2_addr }

    def get_del_file_info(self, root_dir_address, first_cluster):

        file_name = ""
        file_size = 0
        start_cluster = ""

        root_dir_address = int(root_dir_address)

        # create address of sector we need to seek to
        sector_address = root_dir_address * SECTOR_SIZE

        found_deleted = False
        with open(self.filepath, "rb") as f:
            f.seek(0)
            f.seek(sector_address)
            while found_deleted != True:
                part = ""
                byte = f.read(32)
                # read a byte, if a deleted file, get file info
                if binascii.hexlify(byte).upper()[:2] == "E5":
                    found_deleted = True

                    file_name = binascii.hexlify(byte).upper()[:22].decode("hex")
                    start_cluster = self.toBigEndian(binascii.hexlify(byte[-6:-4])).upper()
                    file_size = int(self.toBigEndian(binascii.hexlify(byte[-4:])).upper(), 16)

                    print "File Name:", file_name
                    print "File Size:", size(file_size)
                    print "Cluster Address:", start_cluster + "h or", str(int(start_cluster,16)) + "d"

                else:
                    # seek to next file in root directory
                    f.read(32)
                    continue

            # Calculate cluster sector address
            file_cluster_addr = int(int(first_cluster) + ((int(start_cluster,16) - 2) * 8))

            # Seek to deleted file on disk
            f.seek(file_cluster_addr * SECTOR_SIZE)

            # read 16 bytes of information
            file_data = f.read(16)
            print file_data

def main(argv):
    if argv is None:
        file_path = argv[1]
    else:
        file_path = "/Users/cathal/Dropbox/Masters/Semester 2/EE6012 - Data Forensics/Assignments/diskAnalyser/Sample_1.dd"

    disk_analyser = DiskAnalyser(file_path)
    p_info = disk_analyser.get_partition_information()
    print
    for i in p_info:
        print i
    print

    vol_info = disk_analyser.get_volume_info(p_info[0].get("Sector Start Address"))
    # print vol_info.get("First sector of Data Area")

    disk_analyser.get_del_file_info(vol_info.get("First sector of Data Area"),
                                    vol_info.get("Cluster #2 location"))

    # use this to get sector sizes in decimal
    # print str(int(disk_analyser.toBigEndian("08"), 16))


if __name__ == '__main__':
    main(sys.argv)
