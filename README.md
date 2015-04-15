# diskAnalyser

The aim of this project was to learn more about forensic tools and the basic underlying concepts that are involved with developing such systems as well as how a professional might perform initial analysis of the disk drive or other storage media.
The requirements and goals of this assignment were to develop a small forensic tool which analyses a disk drive for the following:

* Partition Information:
 - The number of partitions.
 - For each partition, display the following:
    * Start sector address.
    * Size of the partition.
    * File system type.
* Volume information of the first partition
  - The number of sectors per cluster.
  - The size of the FAT area.
  - The size of the Root Directory.
  - The sector address of cluster #2.
* Recover the first deleted file in the volume and retrieve the following details about it: o File Name.
  - File Size.
  - First 16 characters of content within the deleted file.

For this project we were given a sample disk image file to analyse, the output was as follows.
![alt tag](http://i.imgur.com/71dOt42.png)

This was a second disk image used to test that the program worked for different disk images
![alt tag](http://i.imgur.com/W3Na3W2.png)
