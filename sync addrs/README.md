# Project synchronization 2 directories from console
Synchronization must be one-way: after the synchronization content of the replica folder should be modified to exactly match content of the source folder;

Synchronization should be performed periodically;

File creation/copying/removal operations should be logged to a file and to the console output;

Folder paths, synchronization interval and log file path should be provided using the command line arguments;

It is undesirable to use third-party libraries that implement folder synchronization;

It is allowed (and recommended) to use external libraries implementing other well-known algorithms. For example, there is no point in implementing yet another function that calculates MD5 if you need it for the task – it is perfectly acceptable to use a third-party (or built-in) library;


script: sync_adrs.py
usage: python sync_adrs.py --zdr_adr "c:\Users\BigBrother\PycharmProjects\python\test_tento" --cil_adr "c:\Users\BigBrother\_copy_test" --perioda 2

script: stop_script.py
usage: python stop_script.py --main_script sync_adrs.py
