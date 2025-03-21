.. _ug_build_system_generators:

Generators: produce and specialize cores on demand
==================================================

.. todo::

   This section was taken from older documentation and needs to be adjusted in style and content for the refactored user guide.

FuseSoC core files list files that are natively used by the backend, such as VHDL/(System)Verilog files, constraints, tcl scripts, hex files for $readmemh, etc. There are however many cases where these files need to be created from another format. Examples of this are Chisel/MyHDL/Migen source code which output verilog, C programs that are compiled into a format suitable to be preloaded into memories or any kind of description formats used to create HDL files. For these cases FuseSoC supports generators, which are a mechanism to generate core files on the fly during the FuseSoC build flow. Since there are too many custom programs to generate HDL files, it is not feasible to include all of them in FuseSoC. Instead they are implemented as stand-alone programs residing within cores, which can be invoked by FuseSoC. Generators consists of three parts:

* The generator itself, which is a stand-alone program residing inside a core. It needs to accept a yaml file with a defined structure described below as its first (and only) argument. The generator will output a valid .core file and output files in the directory where it is called.

* The core that contains a generator must define a section in its core file to let FuseSoC know that it has a generator and how to invoke it.

* A core using a generator must contain a section that describes which parameters to send to the generator, and each target must list which generators to use

Creating a generator
--------------------

Generators can be written in any language. The only requirement is that they are executable on the command line and accepts a yaml file for configuration as its first argument. This also means that generators can be used outside of FuseSoC to create cores. The yaml file contains the configuration needed for the generator. The following options are defined for the configuration file.

========== ===========
Key        Description
========== ===========
gapi       Version of the generator configuration file API. Only 1.0 is defined
files_root Directory where input files are found. FuseSoC sets this to the calling core's file directory
vlnv       Colon-separated VLNV identifier to use for the output core. A generator is free to ignore this and use another VLNV.
parameters Everything contained under the parameters key should be treated as instance-specific configuration for the generator
========== ===========

Example yaml configuration file:

.. code:: yaml

    files_root: /home/user/cores/mysoc
    gapi: '1.0'
    parameters:
      masters:
        dbus:
          slaves: [sdram_dbus, uart0, gpio0, gpio1, spi0]
        or1k_i:
          slaves: [sdram_ibus, rom0]
      slaves:
        gpio0: {datawidth: 8, offset: 2432696320, size: 2}
        gpio1: {datawidth: 8, offset: 2449473536, size: 2}
        rom0: {offset: 4026531840, size: 1024}
        sdram_dbus: {offset: 0, size: 33554432}
        sdram_ibus: {offset: 0, size: 33554432}
        spi0: {datawidth: 8, offset: 2952790016, size: 8}
        uart0: {datawidth: 8, offset: 2415919104, size: 32}
    vlnv: ::mysoc-wb_intercon:0


The above example is for a generator that creates verilog code for a wishbone interconnect.

Registering a generator
-----------------------

When FuseSoC scans the flattened dependency tree of a core, it will look for a section called `generators` in each core file. This section is used by cores to notify FuseSoC that they contain a generator and describe how to use it.

The generators section contain a map of generator sections so that each core is free to define multiple generators. The key of each generator decide its name

The following keys are valid in a generator section.

===================== ===========
Key                   Description
===================== ===========
command               The command to run (relative to the core root) to invoke the generator. FuseSoC will pass a yaml configuration file as the first argument when calling the command.
interpreter           If the command requires an interpreter (e.g. python or perl), this will be used called, with the string specified in `command` as the first argument, and the yaml file as the second argument.
cache_type            If the result of the generator should be considered cacheable. Legal values are `none`, `input` or `generator`.
file_input_parameters All parameters that are file inputs to the generator. This option can be used when `cache_type` is set to `input` if fusesoc should track if these files change.
===================== ===========

Example generator section from a CAPI2 core file

.. code:: yaml

    generators:
      wb_intercon_gen:
        interpreter: python
        command: sw/wb_intercon_gen

The above snippet will register a generator with the name wb_intercon_gen. This name will be used by cores that wish to invoke the generator. When the generator is invoked it will run `python /path/to/core/sw/wb_intercon_gen` from the sw subdirectory of the core where the generators section is defined.

Calling a generator
-------------------

The final piece of the generators machinery is to run a generator with some specific parameters. This is done by creating a special section in the core that wishes to use a generator and adding this section to the targets that need it. Using the same example generator as previously, this section could look like the example below:

.. code:: yaml

    generate:
      wb_intercon:
        generator : wb_intercon_gen
        parameters:
          masters:
            or1k_i:
              slaves:
                - sdram_ibus
                - rom0
            dbus:
              slaves: [sdram_dbus, uart0, gpio0, gpio1, spi0]

          slaves:
            sdram_dbus:
              offset : 0
              size : 0x2000000

            sdram_ibus:
              offset: 0
              size: 0x2000000

            uart0:
              datawidth: 8
              offset: 0x90000000
              size: 32

            gpio0:
              datawidth: 8
              offset: 0x91000000
              size: 2

            gpio1:
              datawidth: 8
              offset: 0x92000000
              size: 2

            spi0:
              datawidth: 8
              offset: 0xb0000000
              size: 8

            rom0:
              offset: 0xf0000000
              size: 1024

The above core file snippet will register a parametrized generator instance with the name wb_intercon. It will use the generator called `wb_intercon_gen` which FuseSoC has previously found in the dependency tree. Everything listed under the `parameters` key is instance-specific configuration to be sent to the generator.

Just registering a generate section will not cause the generator to be invoked. It must also be listed in the target and the generator to be used must be in the dependency tree. The following snippet adds the parameterized generator to the `default` target and adds an explicit dependency on the core that contains the generator. As CAPI2 cores only allow filesets to have dependencies, an empty fileset for this purpose must be created

.. code:: yaml

    filesets:
      wb_intercon_dep:
        depend:
          [wb_intercon]

    targets:
      default:
        filesets : [wb_intercon_dep]
        generate : [wb_intercon]

When FuseSoC is launched and a core target using a generator is processed, the following will happen for each entry in the target's `generate` entry.

1. A key lookup is performed in the core file's `generate` section to find the generator configuration
2. FuseSoC checks that it has registered a generator by the name specified in the `generator` entry of the configuration.
3. FuseSoC calculates a unique VLNV for the generator instance by taking the calling core's VLNV and concatenating the name field with the generator instance name.
4. A directory is created under <cache_root>/generator_cache with a sanitized version of the calculated VLNV along with a SHA256 hash of the input yaml file data appended. This directory is where the output from the generator eventually will appear.
5. If the generator has `cache_type` set to `input` fusesoc will check if a cached output already exists. In this case item 6 and 7 will be omitted. See section :ref:`Generator Cache <ug_generator_cache>` for more information.
6. A yaml configuration file is created in the generator output directory. The parameters from the instance are passed on to this file. FuseSoC will set the files root of the calling core as `files_root` and add the calculated vlnv.
7. FuseSoC will switch working directory to the generator output directory and call the generator, using the command found in the generator's `command` field and with the created yaml file as command-line argument.
8. When the generator has successfully completed (or a cached run already exists), FuseSoC will scan the generator output directory for new .core files. These will be injected in the dependency tree right after the calling core and will be treated just like regular cores, except that any extra dependencies listed in the generated core will be ignored.
9. If the generator is marked as set as cacheable (`input` or `generator`) the directory (along with content) created under item 4 will be kept, otherwise it will be deleted.

.. _ug_generator_cache:

Generator Cache
---------------
Instead of fusesoc rerunning a generator each time and producing the same result it is possible to configure fusesoc to cache generator output and try to detect if a new run would produce the same output. Since there is no generic way of doing this that will fit all generators a couple of different methods for caching and detecting changes are available.

The `generators` option `cache_type` is used for configuring type of caching. If set to `none` (or if option is omitted) no caching will be used. If set to `input` fusesoc will calculate a SHA256 hash of the generator input yaml file data and use this hash for detecting if something has changed and a rerun would be needed. This would happen if some data in the core file `generate` section, for instance `parameters`, has changed.

If `cache_type` is set to `generator` fusesoc will pass the responsibility for detecting if the previous run to the generator is still up to date. In this mode the generator will always be called and the output directory will be saved.

In addition, when `cache_type` is set to `input` it is also possible to configure fusesoc to detect changes in file input data to a generator. This is done by using the `generators` option `file_input_parameters` which tells fusesoc which parameters are used to pass input files to the generator.

Example `generators` section with `cache_type` and `file_input_parameters`:

.. code:: yaml

    generators:
      mytest_gen:
        interpreter: python
        command: mytest_gen.py
        cache_type: input
        file_input_parameters: file_input_param1 file_input_param2


Example `generate` section using the above generator.

.. code:: yaml

    generate:
      mytest:
        generator: mytest_gen
        parameters:
          some_param: 123
          file_input_param1: input_file_1
          file_input_param2: /path/to/input_file_2


In the above example fusesoc would calculate the SHA256 hash for `input_file_1` (relative `files_root`) and `/path/to/input_file_2` (absolute path). This hash would then be saved in the generator cache directory in a file called `.fusesoc_file_input_hash`. During subsequent runs fusesoc would then compare the current input hash with the saved hash to determine if the generator output still is valid or if the generator needs to be run again.

If needed, the `generator_cache` directory under `cache_root` can be cleaned by running `fusesoc gen clean`.
