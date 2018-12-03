class Tcache(GenericCommand):
    """Show tcache status"""
    _cmdline_ = "tcache"
    _syntax_  = "{:s}".format(_cmdline_)
    capsize = 0
    tcache = 0
    tcache_enable = 0
    tcache_bins = 0
    tcache_count = 0

    def init(self):
        self.capsize = current_arch.ptrsize
        self.sbrk_base = int(gdb.execute("p mp_.sbrk_base",to_string=True).split()[2].strip(),16)
        self.tcache_bins = int(gdb.execute("p mp_.tcache_bins",to_string=True).split()[2].strip(),16)
        self.tcache_count = int(gdb.execute("p mp_.tcache_count",to_string=True).split()[2].strip(),16)


    def do_invoke(self, argv):
        self.init()
        counts = {}
        tcache_entry = {}
        chunks = set()

        counts_base = self.sbrk_base + 0x10
        tcache_entry_base = counts_base + self.tcache_bins

        for i in range(self.tcache_bins):
            counts[i] = int(gdb.execute("x/xb " + str(counts_base + i),to_string=True).split()[1].strip(),16)

        for i in range(self.tcache_bins):
            tcache_entry[i] = read_int_from_memory(tcache_entry_base+self.capsize*i)


        print(titlify("Tcache for heap(test function) "+ hex(tcache_entry_base)))

        for i in range(self.tcache_bins):
            if lookup_address(tcache_entry[i]).valid:
                chunk = GlibcChunk(tcache_entry[i])
                gef_print("Tcaches[idx={:d}, size={:#x}, count={:d}] ".format(i,0x10+i*0x10,counts[i]),end="")
                while True:
                    if lookup_address(chunk.address).valid:
                        gef_print("{:s} {:s}".format(LEFT_ARROW,str(chunk)),end='')
                        if chunk.address in chunks:
                            break
                        else:
                            chunks.add(chunk.address)
                        chunk = GlibcChunk(read_int_from_memory(chunk.address))
                    else:
                        break

                print('\n')



        return 0

register_external_command(Tcache())
