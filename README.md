# WinCheck: A Concolic Model Checker for Pointer-Related Properties on Windows Binaries

# Introduction
WinCheck is a model checker that automatically detects pointer-related security properties on Windows executables. The validated properties include buffer overflow, user-after-free, and null-pointer dereference.

# Setup
WinCheck structure:

    benchmark
    src
    LICENSE
    README.md

Prerequisites:

    python3 (>= 3.7.1)
    java (>=11.0.2)
    IDA Pro (>= 7.6)
    
# IDA Pro results

To ensure WinCheck could be applied on the outputs generated by IDA Pro disassembler, we used an *ida_struct.info* file to keep record of all the struct type information defined by IDA Pro disassembler. Currently, the recorded struct type is sufficient for the testing on our benchmark. If you need to test IDA Pro on some other test cases and some of the IDA-defined struct type is unrecognizable, you could add the corresponding information in the *ida_struct.info* file. The *offset* indicates the offset of corresponding item in the struct.

    struct name: 
      item_name: offset, item_type (? represents undefined or unknown type)

# Note

    -- The binary files for Coreutils are located at benchmark/coreutils-5.3.0-bin/bin
    -- The closed-source Windows executables are under the directory benchmark/pe_benchmark
    -- The overall result is stored in a .output file, and the logging information is in a .log file

# Running test cases

Apply WinCheck to detect pointer-related properties for a binary file in the Coreutils library

    $ python -m src.main -e benchmark/coreutils-5.3.0-bin/bin -l benchmark/coreutils-5.3.0-idapro -s 32 -f basename.exe

Use WinCheck to detect pointer-related properties for the whole Coreutils library

    $ python -m src.main -e benchmark/coreutils-5.3.0-bin/bin -l benchmark/coreutils-5.3.0-idapro -s 32 -b

Use WinCheck to detect pointer-related properties for a closed-source Windows executable

    $ python -m src.main -l benchmark/pe_benchmark -e benchmark/pe_benchmark -s 32 -f HOSTNAME.EXE


