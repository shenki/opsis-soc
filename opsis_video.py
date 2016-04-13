#!/usr/bin/env python3
from opsis_base import *

from litevideo.hdmi_in import HDMIIn
from litevideo.hdmi_out import HDMIOut

base_cls = MiniSoC


class VideoMixerSoC(base_cls):
    csr_peripherals = (
        "hdmi_out0",
        "hdmi_out1",
        "hdmi_in0",
        "hdmi_in0_edid_mem",
        "hdmi_in1",
        "hdmi_in1_edid_mem",
    )
    csr_map_update(base_cls.csr_map, csr_peripherals)

    interrupt_map = {
        "hdmi_in0": 3,
        "hdmi_in1": 4,
    }
    interrupt_map.update(base_cls.interrupt_map)

    def __init__(self, platform, **kwargs):
        base_cls.__init__(self, platform, **kwargs)
        self.submodules.hdmi_in0 = HDMIIn(platform.request("hdmi_in", 0),
                                          self.sdram.crossbar.get_master(),
                                          fifo_depth=512)
        self.submodules.hdmi_in1 = HDMIIn(platform.request("hdmi_in", 1),
                                          self.sdram.crossbar.get_master(),
                                          fifo_depth=512)
        self.submodules.hdmi_out0 = HDMIOut(platform.request("hdmi_out", 0),
                                            self.sdram.crossbar.get_master())
        # Share clocking with hdmi_out0 since no PLL_ADV left.
        self.submodules.hdmi_out1 = HDMIOut(platform.request("hdmi_out", 1),
                                            self.sdram.crossbar.get_master(),
                                            self.hdmi_out0.driver.clocking)

        # all PLL_ADV are used: router needs help...
        platform.add_platform_command("""INST PLL_ADV LOC=PLL_ADV_X0Y0;""")
        # FIXME: Fix the HDMI out so this can be removed.
        platform.add_platform_command(
            """PIN "hdmi_out_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command(
            """PIN "hdmi_out_pix_bufg_1.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        platform.add_platform_command(
            """
NET "{pix0_clk}" TNM_NET = "GRPpix0_clk";
NET "{pix1_clk}" TNM_NET = "GRPpix1_clk";
""",
                pix0_clk=self.hdmi_out0.driver.clocking.cd_pix.clk,
                pix1_clk=self.hdmi_out1.driver.clocking.cd_pix.clk,
        )
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.hdmi_out0.driver.clocking.cd_pix.clk,
            self.hdmi_out1.driver.clocking.cd_pix.clk)


def main():
    parser = argparse.ArgumentParser(description="Opsis LiteX SoC")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--nocompile-gateware", action="store_true")
    args = parser.parse_args()

    platform = opsis_platform.Platform()
    soc = VideoMixerSoC(platform, **soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build",
                      compile_gateware=not args.nocompile_gateware,
                      csr_csv="test/csr.csv")
    vns = builder.build()

if __name__ == "__main__":
    main()