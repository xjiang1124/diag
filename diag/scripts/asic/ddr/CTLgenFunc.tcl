#################################

proc mc_0x0_print {} {
    puts "addr: 0x0"
    #fields
    puts "field_name   :START "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :DRAM_CLASS "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0xc "
    puts "field_name   :CONTROLLER_ID "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x0 $data
}

proc mc_0x0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x0]

    return $rdata
}

proc mc_START_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x0 0 1 $data 
} 
 
proc mc_START_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x0 0 1 ] 

    return $rdata 
}

proc mc_DRAM_CLASS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x0 8 4 $data 
} 
 
proc mc_DRAM_CLASS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x0 8 4 ] 

    return $rdata 
}

proc mc_CONTROLLER_ID_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x0 16 16 $data 
} 
 
proc mc_CONTROLLER_ID_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x0 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x3_print {} {
    puts "addr: 0x3"
    #fields
    puts "field_name   :MAX_ROW_REG "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
    puts "field_name   :MAX_COL_REG "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :MAX_CS_REG "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :WRITE_DATA_FIFO_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3 $data
}

proc mc_0x3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3]

    return $rdata
}

proc mc_MAX_ROW_REG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3 0 5 $data 
} 
 
proc mc_MAX_ROW_REG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3 0 5 ] 

    return $rdata 
}

proc mc_MAX_COL_REG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3 8 4 $data 
} 
 
proc mc_MAX_COL_REG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3 8 4 ] 

    return $rdata 
}

proc mc_MAX_CS_REG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3 16 2 $data 
} 
 
proc mc_MAX_CS_REG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3 16 2 ] 

    return $rdata 
}

proc mc_WRITE_DATA_FIFO_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3 24 8 $data 
} 
 
proc mc_WRITE_DATA_FIFO_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x4_print {} {
    puts "addr: 0x4"
    #fields
    puts "field_name   :WRITE_DATA_FIFO_PTR_WIDTH "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :MEMCD_RMODW_FIFO_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :MEMCD_RMODW_FIFO_PTR_WIDTH "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x4 $data
}

proc mc_0x4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x4]

    return $rdata
}

proc mc_WRITE_DATA_FIFO_PTR_WIDTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4 0 8 $data 
} 
 
proc mc_WRITE_DATA_FIFO_PTR_WIDTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4 0 8 ] 

    return $rdata 
}

proc mc_MEMCD_RMODW_FIFO_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4 8 16 $data 
} 
 
proc mc_MEMCD_RMODW_FIFO_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4 8 16 ] 

    return $rdata 
}

proc mc_MEMCD_RMODW_FIFO_PTR_WIDTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4 24 8 $data 
} 
 
proc mc_MEMCD_RMODW_FIFO_PTR_WIDTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x5_print {} {
    puts "addr: 0x5"
    #fields
    puts "field_name   :ASYNC_CDC_STAGES "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_CMDFIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_RDFIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_WR_ARRAY_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x5 $data
}

proc mc_0x5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x5]

    return $rdata
}

proc mc_ASYNC_CDC_STAGES_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5 0 8 $data 
} 
 
proc mc_ASYNC_CDC_STAGES_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5 0 8 ] 

    return $rdata 
}

proc mc_AXI0_CMDFIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5 8 8 $data 
} 
 
proc mc_AXI0_CMDFIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5 8 8 ] 

    return $rdata 
}

proc mc_AXI0_RDFIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5 16 8 $data 
} 
 
proc mc_AXI0_RDFIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5 16 8 ] 

    return $rdata 
}

proc mc_AXI0_WR_ARRAY_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5 24 8 $data 
} 
 
proc mc_AXI0_WR_ARRAY_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x6_print {} {
    puts "addr: 0x6"
    #fields
    puts "field_name   :AXI0_TRANS_WRFIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_WRCMD_PROC_FIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI1_CMDFIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI1_RDFIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x6 $data
}

proc mc_0x6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x6]

    return $rdata
}

proc mc_AXI0_TRANS_WRFIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6 0 8 $data 
} 
 
proc mc_AXI0_TRANS_WRFIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6 0 8 ] 

    return $rdata 
}

proc mc_AXI0_WRCMD_PROC_FIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6 8 8 $data 
} 
 
proc mc_AXI0_WRCMD_PROC_FIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6 8 8 ] 

    return $rdata 
}

proc mc_AXI1_CMDFIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6 16 8 $data 
} 
 
proc mc_AXI1_CMDFIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6 16 8 ] 

    return $rdata 
}

proc mc_AXI1_RDFIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6 24 8 $data 
} 
 
proc mc_AXI1_RDFIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x7_print {} {
    puts "addr: 0x7"
    #fields
    puts "field_name   :AXI1_WR_ARRAY_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI1_TRANS_WRFIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI1_WRCMD_PROC_FIFO_LOG2_DEPTH "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x7 $data
}

proc mc_0x7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x7]

    return $rdata
}

proc mc_AXI1_WR_ARRAY_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7 0 8 $data 
} 
 
proc mc_AXI1_WR_ARRAY_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7 0 8 ] 

    return $rdata 
}

proc mc_AXI1_TRANS_WRFIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7 8 8 $data 
} 
 
proc mc_AXI1_TRANS_WRFIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7 8 8 ] 

    return $rdata 
}

proc mc_AXI1_WRCMD_PROC_FIFO_LOG2_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7 16 8 $data 
} 
 
proc mc_AXI1_WRCMD_PROC_FIFO_LOG2_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7 16 8 ] 

    return $rdata 
}

#################################

proc mc_0xa_print {} {
    puts "addr: 0xa"
    #fields
    puts "field_name   :NO_AUTO_MRR_INIT "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :MRR_ERROR_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :DFI_FREQ_RATIO_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x2 "
} 

proc mc_0xa_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa $data
}

proc mc_0xa_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa]

    return $rdata
}

proc mc_NO_AUTO_MRR_INIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa 8 1 $data 
} 
 
proc mc_NO_AUTO_MRR_INIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa 8 1 ] 

    return $rdata 
}

proc mc_MRR_ERROR_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa 16 1 $data 
} 
 
proc mc_MRR_ERROR_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa 16 1 ] 

    return $rdata 
}

proc mc_DFI_FREQ_RATIO_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa 24 2 $data 
} 
 
proc mc_DFI_FREQ_RATIO_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa 24 2 ] 

    return $rdata 
}

#################################

proc mc_0xb_print {} {
    puts "addr: 0xb"
    #fields
    puts "field_name   :DFI_FREQ_RATIO_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x2 "
    puts "field_name   :DFI_CMD_RATIO "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :PHY_INDEP_TRAIN_MODE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :TSREF2PHYMSTR "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0x10 "
} 

proc mc_0xb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xb $data
}

proc mc_0xb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xb]

    return $rdata
}

proc mc_DFI_FREQ_RATIO_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb 0 2 $data 
} 
 
proc mc_DFI_FREQ_RATIO_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb 0 2 ] 

    return $rdata 
}

proc mc_DFI_CMD_RATIO_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb 8 2 $data 
} 
 
proc mc_DFI_CMD_RATIO_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb 8 2 ] 

    return $rdata 
}

proc mc_PHY_INDEP_TRAIN_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb 16 1 $data 
} 
 
proc mc_PHY_INDEP_TRAIN_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb 16 1 ] 

    return $rdata 
}

proc mc_TSREF2PHYMSTR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb 24 6 $data 
} 
 
proc mc_TSREF2PHYMSTR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb 24 6 ] 

    return $rdata 
}

#################################

proc mc_0xc_print {} {
    puts "addr: 0xc"
    #fields
    puts "field_name   :PHY_INDEP_INIT_MODE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :DFIBUS_FREQ_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
    puts "field_name   :DFIBUS_FREQ_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x1 "
    puts "field_name   :FREQ_CHANGE_TYPE_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc $data
}

proc mc_0xc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc]

    return $rdata
}

proc mc_PHY_INDEP_INIT_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc 0 1 $data 
} 
 
proc mc_PHY_INDEP_INIT_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc 0 1 ] 

    return $rdata 
}

proc mc_DFIBUS_FREQ_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc 8 5 $data 
} 
 
proc mc_DFIBUS_FREQ_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc 8 5 ] 

    return $rdata 
}

proc mc_DFIBUS_FREQ_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc 16 5 $data 
} 
 
proc mc_DFIBUS_FREQ_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc 16 5 ] 

    return $rdata 
}

proc mc_FREQ_CHANGE_TYPE_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc 24 1 $data 
} 
 
proc mc_FREQ_CHANGE_TYPE_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc 24 1 ] 

    return $rdata 
}

#################################

proc mc_0xd_print {} {
    puts "addr: 0xd"
    #fields
    puts "field_name   :FREQ_CHANGE_TYPE_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :LPC_SW_ENTER_DQS_OSC_IN_PROGRESS_ERR_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_PER_CS_OOV_TRAINING_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_TST "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd $data
}

proc mc_0xd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd]

    return $rdata
}

proc mc_FREQ_CHANGE_TYPE_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd 0 1 $data 
} 
 
proc mc_FREQ_CHANGE_TYPE_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd 0 1 ] 

    return $rdata 
}

proc mc_LPC_SW_ENTER_DQS_OSC_IN_PROGRESS_ERR_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd 8 1 $data 
} 
 
proc mc_LPC_SW_ENTER_DQS_OSC_IN_PROGRESS_ERR_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd 8 1 ] 

    return $rdata 
}

proc mc_DQS_OSC_PER_CS_OOV_TRAINING_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd 16 2 $data 
} 
 
proc mc_DQS_OSC_PER_CS_OOV_TRAINING_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd 16 2 ] 

    return $rdata 
}

proc mc_DQS_OSC_TST_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd 24 1 $data 
} 
 
proc mc_DQS_OSC_TST_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd 24 1 ] 

    return $rdata 
}

#################################

proc mc_0xe_print {} {
    puts "addr: 0xe"
    #fields
    puts "field_name   :DQS_OSC_MPC_CMD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :28 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe $data
}

proc mc_0xe_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe]

    return $rdata
}

proc mc_DQS_OSC_MPC_CMD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe 0 28 $data 
} 
 
proc mc_DQS_OSC_MPC_CMD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe 0 28 ] 

    return $rdata 
}

#################################

proc mc_0xf_print {} {
    puts "addr: 0xf"
    #fields
    puts "field_name   :MRR_LSB_REG "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :MRR_MSB_REG "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf $data
}

proc mc_0xf_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf]

    return $rdata
}

proc mc_MRR_LSB_REG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf 0 8 $data 
} 
 
proc mc_MRR_LSB_REG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf 0 8 ] 

    return $rdata 
}

proc mc_MRR_MSB_REG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf 8 8 $data 
} 
 
proc mc_MRR_MSB_REG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf 8 8 ] 

    return $rdata 
}

proc mc_DQS_OSC_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf 16 1 $data 
} 
 
proc mc_DQS_OSC_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf 16 1 ] 

    return $rdata 
}

#################################

proc mc_0x10_print {} {
    puts "addr: 0x10"
    #fields
    puts "field_name   :DQS_OSC_PERIOD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :15 "
    puts "default field_value  :0x200 "
    puts "field_name   :FUNC_VALID_CYCLES "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
} 

proc mc_0x10_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x10 $data
}

proc mc_0x10_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x10]

    return $rdata
}

proc mc_DQS_OSC_PERIOD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x10 0 15 $data 
} 
 
proc mc_DQS_OSC_PERIOD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x10 0 15 ] 

    return $rdata 
}

proc mc_FUNC_VALID_CYCLES_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x10 16 4 $data 
} 
 
proc mc_FUNC_VALID_CYCLES_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x10 16 4 ] 

    return $rdata 
}

#################################

proc mc_0x11_print {} {
    puts "addr: 0x11"
    #fields
    puts "field_name   :DQS_OSC_NORM_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x11_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x11 $data
}

proc mc_0x11_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x11]

    return $rdata
}

proc mc_DQS_OSC_NORM_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11 0 32 $data 
} 
 
proc mc_DQS_OSC_NORM_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x12_print {} {
    puts "addr: 0x12"
    #fields
    puts "field_name   :DQS_OSC_HIGH_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x12_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x12 $data
}

proc mc_0x12_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x12]

    return $rdata
}

proc mc_DQS_OSC_HIGH_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12 0 32 $data 
} 
 
proc mc_DQS_OSC_HIGH_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x13_print {} {
    puts "addr: 0x13"
    #fields
    puts "field_name   :DQS_OSC_TIMEOUT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x13_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x13 $data
}

proc mc_0x13_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x13]

    return $rdata
}

proc mc_DQS_OSC_TIMEOUT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13 0 32 $data 
} 
 
proc mc_DQS_OSC_TIMEOUT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x14_print {} {
    puts "addr: 0x14"
    #fields
    puts "field_name   :DQS_OSC_PROMOTE_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x14_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x14 $data
}

proc mc_0x14_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x14]

    return $rdata
}

proc mc_DQS_OSC_PROMOTE_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14 0 32 $data 
} 
 
proc mc_DQS_OSC_PROMOTE_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x15_print {} {
    puts "addr: 0x15"
    #fields
    puts "field_name   :OSC_VARIANCE_LIMIT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x10 "
    puts "field_name   :DQS_OSC_REQUEST "
    puts "field_access :WR "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :TOSCO_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
} 

proc mc_0x15_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x15 $data
}

proc mc_0x15_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x15]

    return $rdata
}

proc mc_OSC_VARIANCE_LIMIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15 0 16 $data 
} 
 
proc mc_OSC_VARIANCE_LIMIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_REQUEST_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15 16 1 $data 
} 
 
proc mc_DQS_OSC_REQUEST_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15 16 1 ] 

    return $rdata 
}

proc mc_TOSCO_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15 24 8 $data 
} 
 
proc mc_TOSCO_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x16_print {} {
    puts "addr: 0x16"
    #fields
    puts "field_name   :TOSCO_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
} 

proc mc_0x16_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x16 $data
}

proc mc_0x16_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x16]

    return $rdata
}

proc mc_TOSCO_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x16 0 8 $data 
} 
 
proc mc_TOSCO_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x16 0 8 ] 

    return $rdata 
}

#################################

proc mc_0x17_print {} {
    puts "addr: 0x17"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_0_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x17_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x17 $data
}

proc mc_0x17_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x17]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_0_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x17 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_0_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x17 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x18_print {} {
    puts "addr: 0x18"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_1_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_2_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x18_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x18 $data
}

proc mc_0x18_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x18]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_1_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_1_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_2_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_2_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x19_print {} {
    puts "addr: 0x19"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_3_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_4_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x19_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x19 $data
}

proc mc_0x19_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x19]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_3_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_3_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_4_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_4_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x1a_print {} {
    puts "addr: 0x1a"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_5_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_6_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a $data
}

proc mc_0x1a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_5_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_5_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_6_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_6_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x1b_print {} {
    puts "addr: 0x1b"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_7_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_8_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1b $data
}

proc mc_0x1b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1b]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_7_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1b 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_7_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1b 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_8_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1b 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_8_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1b 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x1c_print {} {
    puts "addr: 0x1c"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_9_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_10_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c $data
}

proc mc_0x1c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_9_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_9_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_10_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_10_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x1d_print {} {
    puts "addr: 0x1d"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_11_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_12_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1d $data
}

proc mc_0x1d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1d]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_11_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1d 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_11_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1d 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_12_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1d 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_12_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1d 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x1e_print {} {
    puts "addr: 0x1e"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_13_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_14_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e $data
}

proc mc_0x1e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_13_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_13_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_14_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_14_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x1f_print {} {
    puts "addr: 0x1f"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_15_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_16_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f $data
}

proc mc_0x1f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_15_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_15_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_16_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_16_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x20_print {} {
    puts "addr: 0x20"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_17_CS0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_0_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x20_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x20 $data
}

proc mc_0x20_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x20]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_17_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_17_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_0_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_0_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x21_print {} {
    puts "addr: 0x21"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_1_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_2_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x21_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x21 $data
}

proc mc_0x21_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x21]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_1_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_1_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_2_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_2_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x22_print {} {
    puts "addr: 0x22"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_3_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_4_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x22_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x22 $data
}

proc mc_0x22_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x22]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_3_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_3_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_4_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_4_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x23_print {} {
    puts "addr: 0x23"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_5_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_6_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x23_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x23 $data
}

proc mc_0x23_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x23]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_5_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_5_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_6_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_6_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x24_print {} {
    puts "addr: 0x24"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_7_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_8_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x24_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x24 $data
}

proc mc_0x24_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x24]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_7_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_7_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_8_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_8_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x25_print {} {
    puts "addr: 0x25"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_9_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_10_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x25_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x25 $data
}

proc mc_0x25_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x25]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_9_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_9_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_10_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_10_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x26_print {} {
    puts "addr: 0x26"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_11_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_12_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x26_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x26 $data
}

proc mc_0x26_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x26]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_11_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_11_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_12_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_12_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x27_print {} {
    puts "addr: 0x27"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_13_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_14_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x27_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x27 $data
}

proc mc_0x27_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x27]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_13_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x27 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_13_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x27 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_14_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x27 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_14_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x27 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x28_print {} {
    puts "addr: 0x28"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_15_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_BASE_VALUE_16_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x28_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x28 $data
}

proc mc_0x28_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x28]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_15_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x28 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_15_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x28 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_BASE_VALUE_16_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x28 16 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_16_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x28 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x29_print {} {
    puts "addr: 0x29"
    #fields
    puts "field_name   :DQS_OSC_BASE_VALUE_17_CS1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQS_OSC_IN_PROGRESS_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x29_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x29 $data
}

proc mc_0x29_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x29]

    return $rdata
}

proc mc_DQS_OSC_BASE_VALUE_17_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x29 0 16 $data 
} 
 
proc mc_DQS_OSC_BASE_VALUE_17_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x29 0 16 ] 

    return $rdata 
}

proc mc_DQS_OSC_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x29 16 4 $data 
} 
 
proc mc_DQS_OSC_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x29 16 4 ] 

    return $rdata 
}

proc mc_DQS_OSC_IN_PROGRESS_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x29 24 1 $data 
} 
 
proc mc_DQS_OSC_IN_PROGRESS_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x29 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x2a_print {} {
    puts "addr: 0x2a"
    #fields
    puts "field_name   :RDIMM_CA_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :CASLAT_LIN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x5c "
    puts "field_name   :WRLAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :7 "
    puts "default field_value  :0x2c "
    puts "field_name   :ADDITIVE_LAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0x2a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x2a $data
}

proc mc_0x2a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x2a]

    return $rdata
}

proc mc_RDIMM_CA_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2a 0 1 $data 
} 
 
proc mc_RDIMM_CA_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2a 0 1 ] 

    return $rdata 
}

proc mc_CASLAT_LIN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2a 8 8 $data 
} 
 
proc mc_CASLAT_LIN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2a 8 8 ] 

    return $rdata 
}

proc mc_WRLAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2a 16 7 $data 
} 
 
proc mc_WRLAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2a 16 7 ] 

    return $rdata 
}

proc mc_ADDITIVE_LAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2a 24 7 $data 
} 
 
proc mc_ADDITIVE_LAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2a 24 7 ] 

    return $rdata 
}

#################################

proc mc_0x2b_print {} {
    puts "addr: 0x2b"
    #fields
    puts "field_name   :CA_PARITY_LAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :TCSSR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :TCKSTAB_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x2b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x2b $data
}

proc mc_0x2b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x2b]

    return $rdata
}

proc mc_CA_PARITY_LAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2b 0 4 $data 
} 
 
proc mc_CA_PARITY_LAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2b 0 4 ] 

    return $rdata 
}

proc mc_TCSSR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2b 8 8 $data 
} 
 
proc mc_TCSSR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2b 8 8 ] 

    return $rdata 
}

proc mc_TCKSTAB_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2b 16 16 $data 
} 
 
proc mc_TCKSTAB_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2b 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x2c_print {} {
    puts "addr: 0x2c"
    #fields
    puts "field_name   :TMOD_PAR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :TMRD_PAR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :CASLAT_LIN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x5c "
} 

proc mc_0x2c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x2c $data
}

proc mc_0x2c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x2c]

    return $rdata
}

proc mc_TMOD_PAR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2c 0 8 $data 
} 
 
proc mc_TMOD_PAR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2c 0 8 ] 

    return $rdata 
}

proc mc_TMRD_PAR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2c 8 8 $data 
} 
 
proc mc_TMRD_PAR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2c 8 8 ] 

    return $rdata 
}

proc mc_CASLAT_LIN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2c 24 8 $data 
} 
 
proc mc_CASLAT_LIN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2c 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x2d_print {} {
    puts "addr: 0x2d"
    #fields
    puts "field_name   :WRLAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x2c "
    puts "field_name   :ADDITIVE_LAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :CA_PARITY_LAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :TCSSR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x2d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x2d $data
}

proc mc_0x2d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x2d]

    return $rdata
}

proc mc_WRLAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2d 0 7 $data 
} 
 
proc mc_WRLAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2d 0 7 ] 

    return $rdata 
}

proc mc_ADDITIVE_LAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2d 8 7 $data 
} 
 
proc mc_ADDITIVE_LAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2d 8 7 ] 

    return $rdata 
}

proc mc_CA_PARITY_LAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2d 16 4 $data 
} 
 
proc mc_CA_PARITY_LAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2d 16 4 ] 

    return $rdata 
}

proc mc_TCSSR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2d 24 8 $data 
} 
 
proc mc_TCSSR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2d 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x2e_print {} {
    puts "addr: 0x2e"
    #fields
    puts "field_name   :TCKSTAB_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :TMOD_PAR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x2e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x2e $data
}

proc mc_0x2e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x2e]

    return $rdata
}

proc mc_TCKSTAB_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2e 0 16 $data 
} 
 
proc mc_TCKSTAB_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2e 0 16 ] 

    return $rdata 
}

proc mc_TMOD_PAR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2e 16 8 $data 
} 
 
proc mc_TMOD_PAR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2e 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x2f_print {} {
    puts "addr: 0x2f"
    #fields
    puts "field_name   :TMRD_PAR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :TBST_INT_INTERVAL "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x4 "
    puts "field_name   :TCCD "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x8 "
} 

proc mc_0x2f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x2f $data
}

proc mc_0x2f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x2f]

    return $rdata
}

proc mc_TMRD_PAR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2f 0 8 $data 
} 
 
proc mc_TMRD_PAR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2f 0 8 ] 

    return $rdata 
}

proc mc_TBST_INT_INTERVAL_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2f 16 3 $data 
} 
 
proc mc_TBST_INT_INTERVAL_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2f 16 3 ] 

    return $rdata 
}

proc mc_TCCD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x2f 24 5 $data 
} 
 
proc mc_TCCD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x2f 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x30_print {} {
    puts "addr: 0x30"
    #fields
    puts "field_name   :TCCD_L_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :5 "
    puts "default field_value  :0xe "
    puts "field_name   :TCCD_L_WR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :7 "
    puts "default field_value  :0x3c "
    puts "field_name   :TCCD_L_WR2_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :7 "
    puts "default field_value  :0x1d "
    puts "field_name   :TRRD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x8 "
} 

proc mc_0x30_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x30 $data
}

proc mc_0x30_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x30]

    return $rdata
}

proc mc_TCCD_L_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x30 0 5 $data 
} 
 
proc mc_TCCD_L_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x30 0 5 ] 

    return $rdata 
}

proc mc_TCCD_L_WR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x30 8 7 $data 
} 
 
proc mc_TCCD_L_WR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x30 8 7 ] 

    return $rdata 
}

proc mc_TCCD_L_WR2_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x30 16 7 $data 
} 
 
proc mc_TCCD_L_WR2_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x30 16 7 ] 

    return $rdata 
}

proc mc_TRRD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x30 24 8 $data 
} 
 
proc mc_TRRD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x30 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x31_print {} {
    puts "addr: 0x31"
    #fields
    puts "field_name   :TRRD_L_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0xf "
    puts "field_name   :TRC_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :9 "
    puts "default field_value  :0x87 "
} 

proc mc_0x31_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x31 $data
}

proc mc_0x31_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x31]

    return $rdata
}

proc mc_TRRD_L_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31 0 8 $data 
} 
 
proc mc_TRRD_L_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31 0 8 ] 

    return $rdata 
}

proc mc_TRC_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31 8 9 $data 
} 
 
proc mc_TRC_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31 8 9 ] 

    return $rdata 
}

#################################

proc mc_0x32_print {} {
    puts "addr: 0x32"
    #fields
    puts "field_name   :TRAS_MIN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x5a "
    puts "field_name   :TWTR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :7 "
    puts "default field_value  :0x8 "
    puts "field_name   :TWTR_L_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :7 "
    puts "default field_value  :0x1e "
} 

proc mc_0x32_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x32 $data
}

proc mc_0x32_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x32]

    return $rdata
}

proc mc_TRAS_MIN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32 0 9 $data 
} 
 
proc mc_TRAS_MIN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32 0 9 ] 

    return $rdata 
}

proc mc_TWTR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32 16 7 $data 
} 
 
proc mc_TWTR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32 16 7 ] 

    return $rdata 
}

proc mc_TWTR_L_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32 24 7 $data 
} 
 
proc mc_TWTR_L_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32 24 7 ] 

    return $rdata 
}

#################################

proc mc_0x33_print {} {
    puts "addr: 0x33"
    #fields
    puts "field_name   :TWTR_AP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x40 "
    puts "field_name   :TWTR_L_AP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x40 "
} 

proc mc_0x33_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x33 $data
}

proc mc_0x33_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x33]

    return $rdata
}

proc mc_TWTR_AP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33 0 9 $data 
} 
 
proc mc_TWTR_AP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33 0 9 ] 

    return $rdata 
}

proc mc_TWTR_L_AP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33 16 9 $data 
} 
 
proc mc_TWTR_L_AP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x34_print {} {
    puts "addr: 0x34"
    #fields
    puts "field_name   :TRP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x2f "
    puts "field_name   :TFAW_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :9 "
    puts "default field_value  :0x21 "
    puts "field_name   :TCCD_L_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0xe "
} 

proc mc_0x34_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x34 $data
}

proc mc_0x34_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x34]

    return $rdata
}

proc mc_TRP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34 0 8 $data 
} 
 
proc mc_TRP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34 0 8 ] 

    return $rdata 
}

proc mc_TFAW_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34 8 9 $data 
} 
 
proc mc_TFAW_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34 8 9 ] 

    return $rdata 
}

proc mc_TCCD_L_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34 24 5 $data 
} 
 
proc mc_TCCD_L_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x35_print {} {
    puts "addr: 0x35"
    #fields
    puts "field_name   :TCCD_L_WR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x3c "
    puts "field_name   :TCCD_L_WR2_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :7 "
    puts "default field_value  :0x1d "
    puts "field_name   :TRRD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x8 "
    puts "field_name   :TRRD_L_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0xf "
} 

proc mc_0x35_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x35 $data
}

proc mc_0x35_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x35]

    return $rdata
}

proc mc_TCCD_L_WR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35 0 7 $data 
} 
 
proc mc_TCCD_L_WR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35 0 7 ] 

    return $rdata 
}

proc mc_TCCD_L_WR2_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35 8 7 $data 
} 
 
proc mc_TCCD_L_WR2_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35 8 7 ] 

    return $rdata 
}

proc mc_TRRD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35 16 8 $data 
} 
 
proc mc_TRRD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35 16 8 ] 

    return $rdata 
}

proc mc_TRRD_L_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35 24 8 $data 
} 
 
proc mc_TRRD_L_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x36_print {} {
    puts "addr: 0x36"
    #fields
    puts "field_name   :TRC_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x87 "
    puts "field_name   :TRAS_MIN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x5a "
} 

proc mc_0x36_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x36 $data
}

proc mc_0x36_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x36]

    return $rdata
}

proc mc_TRC_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36 0 9 $data 
} 
 
proc mc_TRC_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36 0 9 ] 

    return $rdata 
}

proc mc_TRAS_MIN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36 16 9 $data 
} 
 
proc mc_TRAS_MIN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x37_print {} {
    puts "addr: 0x37"
    #fields
    puts "field_name   :TWTR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x8 "
    puts "field_name   :TWTR_L_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :7 "
    puts "default field_value  :0x1e "
    puts "field_name   :TWTR_AP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x40 "
} 

proc mc_0x37_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x37 $data
}

proc mc_0x37_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x37]

    return $rdata
}

proc mc_TWTR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37 0 7 $data 
} 
 
proc mc_TWTR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37 0 7 ] 

    return $rdata 
}

proc mc_TWTR_L_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37 8 7 $data 
} 
 
proc mc_TWTR_L_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37 8 7 ] 

    return $rdata 
}

proc mc_TWTR_AP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37 16 9 $data 
} 
 
proc mc_TWTR_AP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x38_print {} {
    puts "addr: 0x38"
    #fields
    puts "field_name   :TWTR_L_AP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x40 "
    puts "field_name   :TRP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x2f "
} 

proc mc_0x38_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x38 $data
}

proc mc_0x38_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x38]

    return $rdata
}

proc mc_TWTR_L_AP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38 0 9 $data 
} 
 
proc mc_TWTR_L_AP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38 0 9 ] 

    return $rdata 
}

proc mc_TRP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38 16 8 $data 
} 
 
proc mc_TRP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x39_print {} {
    puts "addr: 0x39"
    #fields
    puts "field_name   :TFAW_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x21 "
    puts "field_name   :TRTP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x17 "
    puts "field_name   :TRTP_AP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x17 "
} 

proc mc_0x39_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x39 $data
}

proc mc_0x39_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x39]

    return $rdata
}

proc mc_TFAW_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39 0 9 $data 
} 
 
proc mc_TFAW_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39 0 9 ] 

    return $rdata 
}

proc mc_TRTP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39 16 8 $data 
} 
 
proc mc_TRTP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39 16 8 ] 

    return $rdata 
}

proc mc_TRTP_AP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39 24 8 $data 
} 
 
proc mc_TRTP_AP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x3a_print {} {
    puts "addr: 0x3a"
    #fields
    puts "field_name   :TMPC_DELAY_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
    puts "field_name   :TMRD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
    puts "field_name   :TMOD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
} 

proc mc_0x3a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a $data
}

proc mc_0x3a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a]

    return $rdata
}

proc mc_TMPC_DELAY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a 0 8 $data 
} 
 
proc mc_TMPC_DELAY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a 0 8 ] 

    return $rdata 
}

proc mc_TMRD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a 8 8 $data 
} 
 
proc mc_TMRD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a 8 8 ] 

    return $rdata 
}

proc mc_TMOD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a 24 8 $data 
} 
 
proc mc_TMOD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x3b_print {} {
    puts "addr: 0x3b"
    #fields
    puts "field_name   :TRAS_MAX_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :20 "
    puts "default field_value  :0xd55d "
    puts "field_name   :TCKE_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0x16 "
} 

proc mc_0x3b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b $data
}

proc mc_0x3b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b]

    return $rdata
}

proc mc_TRAS_MAX_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b 0 20 $data 
} 
 
proc mc_TRAS_MAX_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b 0 20 ] 

    return $rdata 
}

proc mc_TCKE_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b 24 6 $data 
} 
 
proc mc_TCKE_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b 24 6 ] 

    return $rdata 
}

#################################

proc mc_0x3c_print {} {
    puts "addr: 0x3c"
    #fields
    puts "field_name   :TCKESR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x1d "
    puts "field_name   :TRTP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x17 "
    puts "field_name   :TRTP_AP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x17 "
    puts "field_name   :TMPC_DELAY_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
} 

proc mc_0x3c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3c $data
}

proc mc_0x3c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3c]

    return $rdata
}

proc mc_TCKESR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3c 0 8 $data 
} 
 
proc mc_TCKESR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3c 0 8 ] 

    return $rdata 
}

proc mc_TRTP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3c 8 8 $data 
} 
 
proc mc_TRTP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3c 8 8 ] 

    return $rdata 
}

proc mc_TRTP_AP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3c 16 8 $data 
} 
 
proc mc_TRTP_AP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3c 16 8 ] 

    return $rdata 
}

proc mc_TMPC_DELAY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3c 24 8 $data 
} 
 
proc mc_TMPC_DELAY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3c 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x3d_print {} {
    puts "addr: 0x3d"
    #fields
    puts "field_name   :TMRD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
    puts "field_name   :TMOD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
} 

proc mc_0x3d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3d $data
}

proc mc_0x3d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3d]

    return $rdata
}

proc mc_TMRD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3d 0 8 $data 
} 
 
proc mc_TMRD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3d 0 8 ] 

    return $rdata 
}

proc mc_TMOD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3d 16 8 $data 
} 
 
proc mc_TMOD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3d 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x3e_print {} {
    puts "addr: 0x3e"
    #fields
    puts "field_name   :TRAS_MAX_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :20 "
    puts "default field_value  :0xd55d "
    puts "field_name   :TCKE_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0x16 "
} 

proc mc_0x3e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3e $data
}

proc mc_0x3e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3e]

    return $rdata
}

proc mc_TRAS_MAX_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3e 0 20 $data 
} 
 
proc mc_TRAS_MAX_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3e 0 20 ] 

    return $rdata 
}

proc mc_TCKE_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3e 24 6 $data 
} 
 
proc mc_TCKE_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3e 24 6 ] 

    return $rdata 
}

#################################

proc mc_0x3f_print {} {
    puts "addr: 0x3f"
    #fields
    puts "field_name   :TCKESR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x1d "
    puts "field_name   :TPPD_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x2 "
    puts "field_name   :TPPD_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x2 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x3 "
} 

proc mc_0x3f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3f $data
}

proc mc_0x3f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3f]

    return $rdata
}

proc mc_TCKESR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3f 0 8 $data 
} 
 
proc mc_TCKESR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3f 0 8 ] 

    return $rdata 
}

proc mc_TPPD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3f 8 3 $data 
} 
 
proc mc_TPPD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3f 8 3 ] 

    return $rdata 
}

proc mc_TPPD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3f 16 3 $data 
} 
 
proc mc_TPPD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3f 16 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3f 24 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3f 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x40_print {} {
    puts "addr: 0x40"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x3 "
    puts "field_name   :WRITEINTERP "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :MPC_MULTI_CYCLE_ENABLE_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :MPC_MULTI_CYCLE_ENABLE_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x40_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x40 $data
}

proc mc_0x40_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x40]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x40 0 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x40 0 3 ] 

    return $rdata 
}

proc mc_WRITEINTERP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x40 8 1 $data 
} 
 
proc mc_WRITEINTERP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x40 8 1 ] 

    return $rdata 
}

proc mc_MPC_MULTI_CYCLE_ENABLE_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x40 16 1 $data 
} 
 
proc mc_MPC_MULTI_CYCLE_ENABLE_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x40 16 1 ] 

    return $rdata 
}

proc mc_MPC_MULTI_CYCLE_ENABLE_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x40 24 1 $data 
} 
 
proc mc_MPC_MULTI_CYCLE_ENABLE_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x40 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x41_print {} {
    puts "addr: 0x41"
    #fields
    puts "field_name   :TMPC_CS_LOW "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x4 "
    puts "field_name   :TMPC_SETUP "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x3 "
    puts "field_name   :TMPC_HOLD "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x3 "
    puts "field_name   :MPC_REQ "
    puts "field_access :WR "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x41_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x41 $data
}

proc mc_0x41_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x41]

    return $rdata
}

proc mc_TMPC_CS_LOW_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x41 0 4 $data 
} 
 
proc mc_TMPC_CS_LOW_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x41 0 4 ] 

    return $rdata 
}

proc mc_TMPC_SETUP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x41 8 4 $data 
} 
 
proc mc_TMPC_SETUP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x41 8 4 ] 

    return $rdata 
}

proc mc_TMPC_HOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x41 16 4 $data 
} 
 
proc mc_TMPC_HOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x41 16 4 ] 

    return $rdata 
}

proc mc_MPC_REQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x41 24 1 $data 
} 
 
proc mc_MPC_REQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x41 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x42_print {} {
    puts "addr: 0x42"
    #fields
    puts "field_name   :MPC_CS "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :MPC_OPCODE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x42_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x42 $data
}

proc mc_0x42_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x42]

    return $rdata
}

proc mc_MPC_CS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x42 0 2 $data 
} 
 
proc mc_MPC_CS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x42 0 2 ] 

    return $rdata 
}

proc mc_MPC_OPCODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x42 8 8 $data 
} 
 
proc mc_MPC_OPCODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x42 8 8 ] 

    return $rdata 
}

#################################

proc mc_0x43_print {} {
    puts "addr: 0x43"
    #fields
    puts "field_name   :MPC_PROMOTE_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x43_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x43 $data
}

proc mc_0x43_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x43]

    return $rdata
}

proc mc_MPC_PROMOTE_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x43 0 32 $data 
} 
 
proc mc_MPC_PROMOTE_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x43 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x44_print {} {
    puts "addr: 0x44"
    #fields
    puts "field_name   :MPC_ERROR_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :TRCD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x2d "
    puts "field_name   :TWR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x5a "
    puts "field_name   :TRCD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x2d "
} 

proc mc_0x44_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x44 $data
}

proc mc_0x44_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x44]

    return $rdata
}

proc mc_MPC_ERROR_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x44 0 1 $data 
} 
 
proc mc_MPC_ERROR_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x44 0 1 ] 

    return $rdata 
}

proc mc_TRCD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x44 8 8 $data 
} 
 
proc mc_TRCD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x44 8 8 ] 

    return $rdata 
}

proc mc_TWR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x44 16 8 $data 
} 
 
proc mc_TWR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x44 16 8 ] 

    return $rdata 
}

proc mc_TRCD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x44 24 8 $data 
} 
 
proc mc_TRCD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x44 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x45_print {} {
    puts "addr: 0x45"
    #fields
    puts "field_name   :TWR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x5a "
    puts "field_name   :TMRR "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
    puts "field_name   :TMPRR "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :AP "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x45_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x45 $data
}

proc mc_0x45_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x45]

    return $rdata
}

proc mc_TWR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x45 0 8 $data 
} 
 
proc mc_TWR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x45 0 8 ] 

    return $rdata 
}

proc mc_TMRR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x45 8 8 $data 
} 
 
proc mc_TMRR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x45 8 8 ] 

    return $rdata 
}

proc mc_TMPRR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x45 16 4 $data 
} 
 
proc mc_TMPRR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x45 16 4 ] 

    return $rdata 
}

proc mc_AP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x45 24 1 $data 
} 
 
proc mc_AP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x45 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x46_print {} {
    puts "addr: 0x46"
    #fields
    puts "field_name   :CONCURRENTAP "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :TRAS_LOCKOUT "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :TDAL_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x89 "
    puts "field_name   :TDAL_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x89 "
} 

proc mc_0x46_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x46 $data
}

proc mc_0x46_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x46]

    return $rdata
}

proc mc_CONCURRENTAP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x46 0 1 $data 
} 
 
proc mc_CONCURRENTAP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x46 0 1 ] 

    return $rdata 
}

proc mc_TRAS_LOCKOUT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x46 8 1 $data 
} 
 
proc mc_TRAS_LOCKOUT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x46 8 1 ] 

    return $rdata 
}

proc mc_TDAL_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x46 16 8 $data 
} 
 
proc mc_TDAL_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x46 16 8 ] 

    return $rdata 
}

proc mc_TDAL_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x46 24 8 $data 
} 
 
proc mc_TDAL_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x46 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x47_print {} {
    puts "addr: 0x47"
    #fields
    puts "field_name   :BSTLEN "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :6 "
    puts "default field_value  :0x4 "
    puts "field_name   :TRP_AB_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x30 "
    puts "field_name   :TRP_AB_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x30 "
    puts "field_name   :TRP_AB_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x30 "
} 

proc mc_0x47_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x47 $data
}

proc mc_0x47_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x47]

    return $rdata
}

proc mc_BSTLEN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x47 0 6 $data 
} 
 
proc mc_BSTLEN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x47 0 6 ] 

    return $rdata 
}

proc mc_TRP_AB_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x47 8 8 $data 
} 
 
proc mc_TRP_AB_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x47 8 8 ] 

    return $rdata 
}

proc mc_TRP_AB_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x47 16 8 $data 
} 
 
proc mc_TRP_AB_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x47 16 8 ] 

    return $rdata 
}

proc mc_TRP_AB_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x47 24 8 $data 
} 
 
proc mc_TRP_AB_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x47 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x48_print {} {
    puts "addr: 0x48"
    #fields
    puts "field_name   :TRP_AB_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x30 "
    puts "field_name   :REG_DIMM_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ADDRESS_MIRRORING "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :ADDRESS_INVERSION "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x48_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x48 $data
}

proc mc_0x48_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x48]

    return $rdata
}

proc mc_TRP_AB_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x48 0 8 $data 
} 
 
proc mc_TRP_AB_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x48 0 8 ] 

    return $rdata 
}

proc mc_REG_DIMM_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x48 8 1 $data 
} 
 
proc mc_REG_DIMM_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x48 8 1 ] 

    return $rdata 
}

proc mc_ADDRESS_MIRRORING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x48 16 2 $data 
} 
 
proc mc_ADDRESS_MIRRORING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x48 16 2 ] 

    return $rdata 
}

proc mc_ADDRESS_INVERSION_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x48 24 2 $data 
} 
 
proc mc_ADDRESS_INVERSION_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x48 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x49_print {} {
    puts "addr: 0x49"
    #fields
    puts "field_name   :PDA_INVERT_DEV_CS0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :PDA_INVERT_DEV_CS1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :PDA_INVERT_ECC_DEV_CS0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :PDA_INVERT_ECC_DEV_CS1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x49_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x49 $data
}

proc mc_0x49_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x49]

    return $rdata
}

proc mc_PDA_INVERT_DEV_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x49 0 8 $data 
} 
 
proc mc_PDA_INVERT_DEV_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x49 0 8 ] 

    return $rdata 
}

proc mc_PDA_INVERT_DEV_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x49 8 8 $data 
} 
 
proc mc_PDA_INVERT_DEV_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x49 8 8 ] 

    return $rdata 
}

proc mc_PDA_INVERT_ECC_DEV_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x49 16 1 $data 
} 
 
proc mc_PDA_INVERT_ECC_DEV_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x49 16 1 ] 

    return $rdata 
}

proc mc_PDA_INVERT_ECC_DEV_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x49 24 1 $data 
} 
 
proc mc_PDA_INVERT_ECC_DEV_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x49 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x4a_print {} {
    puts "addr: 0x4a"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :OPTIMAL_RMODW_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x4a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x4a $data
}

proc mc_0x4a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x4a]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4a 0 2 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4a 0 2 ] 

    return $rdata 
}

proc mc_OPTIMAL_RMODW_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4a 16 1 $data 
} 
 
proc mc_OPTIMAL_RMODW_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4a 16 1 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4a 24 1 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4a 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x4b_print {} {
    puts "addr: 0x4b"
    #fields
    puts "field_name   :NO_MEMORY_DM "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x4b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x4b $data
}

proc mc_0x4b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x4b]

    return $rdata
}

proc mc_NO_MEMORY_DM_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4b 0 1 $data 
} 
 
proc mc_NO_MEMORY_DM_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4b 0 1 ] 

    return $rdata 
}

#################################

proc mc_0x4c_print {} {
    puts "addr: 0x4c"
    #fields
    puts "field_name   :CWW_SW_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x4c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x4c $data
}

proc mc_0x4c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x4c]

    return $rdata
}

proc mc_CWW_SW_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4c 8 16 $data 
} 
 
proc mc_CWW_SW_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4c 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x4d_print {} {
    puts "addr: 0x4d"
    #fields
    puts "field_name   :CWW_SW_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :RDIMM_CWW_ERROR_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x4d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x4d $data
}

proc mc_0x4d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x4d]

    return $rdata
}

proc mc_CWW_SW_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4d 0 16 $data 
} 
 
proc mc_CWW_SW_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4d 0 16 ] 

    return $rdata 
}

proc mc_RDIMM_CWW_ERROR_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4d 16 1 $data 
} 
 
proc mc_RDIMM_CWW_ERROR_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4d 16 1 ] 

    return $rdata 
}

#################################

proc mc_0x4e_print {} {
    puts "addr: 0x4e"
    #fields
    puts "field_name   :RDIMM_TMRD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x28 "
} 

proc mc_0x4e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x4e $data
}

proc mc_0x4e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x4e]

    return $rdata
}

proc mc_RDIMM_TMRD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4e 0 8 $data 
} 
 
proc mc_RDIMM_TMRD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4e 0 8 ] 

    return $rdata 
}

#################################

proc mc_0x4f_print {} {
    puts "addr: 0x4f"
    #fields
    puts "field_name   :RDIMM_CTL_F0_0_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x24000065 "
} 

proc mc_0x4f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x4f $data
}

proc mc_0x4f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x4f]

    return $rdata
}

proc mc_RDIMM_CTL_F0_0_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x4f 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_0_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x4f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x50_print {} {
    puts "addr: 0x50"
    #fields
    puts "field_name   :RDIMM_CTL_F0_0_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x1370 "
} 

proc mc_0x50_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x50 $data
}

proc mc_0x50_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x50]

    return $rdata
}

proc mc_RDIMM_CTL_F0_0_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x50 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_0_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x50 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x51_print {} {
    puts "addr: 0x51"
    #fields
    puts "field_name   :RDIMM_CTL_F0_0_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x51_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x51 $data
}

proc mc_0x51_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x51]

    return $rdata
}

proc mc_RDIMM_CTL_F0_0_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x51 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_0_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x51 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x52_print {} {
    puts "addr: 0x52"
    #fields
    puts "field_name   :RDIMM_CTL_F0_0_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x52_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x52 $data
}

proc mc_0x52_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x52]

    return $rdata
}

proc mc_RDIMM_CTL_F0_0_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x52 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_0_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x52 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x53_print {} {
    puts "addr: 0x53"
    #fields
    puts "field_name   :RDIMM_CTL_F0_0_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0x53_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x53 $data
}

proc mc_0x53_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x53]

    return $rdata
}

proc mc_RDIMM_CTL_F0_0_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x53 0 24 $data 
} 
 
proc mc_RDIMM_CTL_F0_0_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x53 0 24 ] 

    return $rdata 
}

#################################

proc mc_0x54_print {} {
    puts "addr: 0x54"
    #fields
    puts "field_name   :RDIMM_CTL_F1_0_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x24000065 "
} 

proc mc_0x54_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x54 $data
}

proc mc_0x54_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x54]

    return $rdata
}

proc mc_RDIMM_CTL_F1_0_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x54 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_0_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x54 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x55_print {} {
    puts "addr: 0x55"
    #fields
    puts "field_name   :RDIMM_CTL_F1_0_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x1370 "
} 

proc mc_0x55_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x55 $data
}

proc mc_0x55_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x55]

    return $rdata
}

proc mc_RDIMM_CTL_F1_0_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x55 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_0_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x55 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x56_print {} {
    puts "addr: 0x56"
    #fields
    puts "field_name   :RDIMM_CTL_F1_0_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x56_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x56 $data
}

proc mc_0x56_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x56]

    return $rdata
}

proc mc_RDIMM_CTL_F1_0_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x56 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_0_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x56 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x57_print {} {
    puts "addr: 0x57"
    #fields
    puts "field_name   :RDIMM_CTL_F1_0_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x57_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x57 $data
}

proc mc_0x57_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x57]

    return $rdata
}

proc mc_RDIMM_CTL_F1_0_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x57 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_0_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x57 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x58_print {} {
    puts "addr: 0x58"
    #fields
    puts "field_name   :RDIMM_CTL_F1_0_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0x58_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x58 $data
}

proc mc_0x58_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x58]

    return $rdata
}

proc mc_RDIMM_CTL_F1_0_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x58 0 24 $data 
} 
 
proc mc_RDIMM_CTL_F1_0_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x58 0 24 ] 

    return $rdata 
}

#################################

proc mc_0x59_print {} {
    puts "addr: 0x59"
    #fields
    puts "field_name   :RDIMM_CTL_F0_1_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x13000154 "
} 

proc mc_0x59_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x59 $data
}

proc mc_0x59_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x59]

    return $rdata
}

proc mc_RDIMM_CTL_F0_1_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x59 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_1_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x59 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x5a_print {} {
    puts "addr: 0x5a"
    #fields
    puts "field_name   :RDIMM_CTL_F0_1_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x1367 "
} 

proc mc_0x5a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x5a $data
}

proc mc_0x5a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x5a]

    return $rdata
}

proc mc_RDIMM_CTL_F0_1_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5a 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_1_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x5b_print {} {
    puts "addr: 0x5b"
    #fields
    puts "field_name   :RDIMM_CTL_F0_1_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x5b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x5b $data
}

proc mc_0x5b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x5b]

    return $rdata
}

proc mc_RDIMM_CTL_F0_1_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5b 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_1_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x5c_print {} {
    puts "addr: 0x5c"
    #fields
    puts "field_name   :RDIMM_CTL_F0_1_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x5c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x5c $data
}

proc mc_0x5c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x5c]

    return $rdata
}

proc mc_RDIMM_CTL_F0_1_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5c 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F0_1_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x5d_print {} {
    puts "addr: 0x5d"
    #fields
    puts "field_name   :RDIMM_CTL_F0_1_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0x5d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x5d $data
}

proc mc_0x5d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x5d]

    return $rdata
}

proc mc_RDIMM_CTL_F0_1_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5d 0 24 $data 
} 
 
proc mc_RDIMM_CTL_F0_1_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5d 0 24 ] 

    return $rdata 
}

#################################

proc mc_0x5e_print {} {
    puts "addr: 0x5e"
    #fields
    puts "field_name   :RDIMM_CTL_F1_1_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x13000154 "
} 

proc mc_0x5e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x5e $data
}

proc mc_0x5e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x5e]

    return $rdata
}

proc mc_RDIMM_CTL_F1_1_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5e 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_1_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x5f_print {} {
    puts "addr: 0x5f"
    #fields
    puts "field_name   :RDIMM_CTL_F1_1_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x1367 "
} 

proc mc_0x5f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x5f $data
}

proc mc_0x5f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x5f]

    return $rdata
}

proc mc_RDIMM_CTL_F1_1_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x5f 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_1_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x5f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x60_print {} {
    puts "addr: 0x60"
    #fields
    puts "field_name   :RDIMM_CTL_F1_1_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x60_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x60 $data
}

proc mc_0x60_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x60]

    return $rdata
}

proc mc_RDIMM_CTL_F1_1_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x60 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_1_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x60 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x61_print {} {
    puts "addr: 0x61"
    #fields
    puts "field_name   :RDIMM_CTL_F1_1_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x61_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x61 $data
}

proc mc_0x61_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x61]

    return $rdata
}

proc mc_RDIMM_CTL_F1_1_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x61 0 32 $data 
} 
 
proc mc_RDIMM_CTL_F1_1_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x61 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x62_print {} {
    puts "addr: 0x62"
    #fields
    puts "field_name   :RDIMM_CTL_F1_1_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0x62_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x62 $data
}

proc mc_0x62_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x62]

    return $rdata
}

proc mc_RDIMM_CTL_F1_1_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x62 0 24 $data 
} 
 
proc mc_RDIMM_CTL_F1_1_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x62 0 24 ] 

    return $rdata 
}

#################################

proc mc_0x63_print {} {
    puts "addr: 0x63"
    #fields
    puts "field_name   :RDIMM_DFS_CW_MAP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :27 "
    puts "default field_value  :0xfff "
} 

proc mc_0x63_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x63 $data
}

proc mc_0x63_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x63]

    return $rdata
}

proc mc_RDIMM_DFS_CW_MAP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x63 0 27 $data 
} 
 
proc mc_RDIMM_DFS_CW_MAP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x63 0 27 ] 

    return $rdata 
}

#################################

proc mc_0x64_print {} {
    puts "addr: 0x64"
    #fields
    puts "field_name   :RDIMM_DFS_CW_MAP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :27 "
    puts "default field_value  :0xfff "
} 

proc mc_0x64_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x64 $data
}

proc mc_0x64_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x64]

    return $rdata
}

proc mc_RDIMM_DFS_CW_MAP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x64 0 27 $data 
} 
 
proc mc_RDIMM_DFS_CW_MAP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x64 0 27 ] 

    return $rdata 
}

#################################

proc mc_0x65_print {} {
    puts "addr: 0x65"
    #fields
    puts "field_name   :RDIMM_CW_MAP "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :27 "
    puts "default field_value  :0xfff "
} 

proc mc_0x65_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x65 $data
}

proc mc_0x65_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x65]

    return $rdata
}

proc mc_RDIMM_CW_MAP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x65 0 27 $data 
} 
 
proc mc_RDIMM_CW_MAP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x65 0 27 ] 

    return $rdata 
}

#################################

proc mc_0x66_print {} {
    puts "addr: 0x66"
    #fields
    puts "field_name   :RDIMM_CW_HOLD_CKE_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :RDIMM_TSTAB_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :24 "
    puts "default field_value  :0x41a7 "
} 

proc mc_0x66_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x66 $data
}

proc mc_0x66_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x66]

    return $rdata
}

proc mc_RDIMM_CW_HOLD_CKE_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x66 0 1 $data 
} 
 
proc mc_RDIMM_CW_HOLD_CKE_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x66 0 1 ] 

    return $rdata 
}

proc mc_RDIMM_TSTAB_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x66 8 24 $data 
} 
 
proc mc_RDIMM_TSTAB_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x66 8 24 ] 

    return $rdata 
}

#################################

proc mc_0x67_print {} {
    puts "addr: 0x67"
    #fields
    puts "field_name   :RDIMM_TSTAB_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x41a7 "
    puts "field_name   :CS_MAP_DIMM_0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
} 

proc mc_0x67_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x67 $data
}

proc mc_0x67_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x67]

    return $rdata
}

proc mc_RDIMM_TSTAB_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x67 0 24 $data 
} 
 
proc mc_RDIMM_TSTAB_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x67 0 24 ] 

    return $rdata 
}

proc mc_CS_MAP_DIMM_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x67 24 2 $data 
} 
 
proc mc_CS_MAP_DIMM_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x67 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x68_print {} {
    puts "addr: 0x68"
    #fields
    puts "field_name   :CS_MAP_DIMM_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :RANK0_MAP_DIMM_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x1 "
    puts "field_name   :RANK0_MAP_DIMM_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :RDIMM_TMRD_L "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x10 "
} 

proc mc_0x68_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x68 $data
}

proc mc_0x68_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x68]

    return $rdata
}

proc mc_CS_MAP_DIMM_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x68 0 2 $data 
} 
 
proc mc_CS_MAP_DIMM_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x68 0 2 ] 

    return $rdata 
}

proc mc_RANK0_MAP_DIMM_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x68 8 2 $data 
} 
 
proc mc_RANK0_MAP_DIMM_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x68 8 2 ] 

    return $rdata 
}

proc mc_RANK0_MAP_DIMM_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x68 16 2 $data 
} 
 
proc mc_RANK0_MAP_DIMM_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x68 16 2 ] 

    return $rdata 
}

proc mc_RDIMM_TMRD_L_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x68 24 5 $data 
} 
 
proc mc_RDIMM_TMRD_L_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x68 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x69_print {} {
    puts "addr: 0x69"
    #fields
    puts "field_name   :RDIMM_TMRD_L2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :6 "
    puts "default field_value  :0x20 "
    puts "field_name   :RDIMM_TMRC "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x10 "
} 

proc mc_0x69_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x69 $data
}

proc mc_0x69_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x69]

    return $rdata
}

proc mc_RDIMM_TMRD_L2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x69 0 6 $data 
} 
 
proc mc_RDIMM_TMRD_L2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x69 0 6 ] 

    return $rdata 
}

proc mc_RDIMM_TMRC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x69 8 5 $data 
} 
 
proc mc_RDIMM_TMRC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x69 8 5 ] 

    return $rdata 
}

#################################

proc mc_0x6d_print {} {
    puts "addr: 0x6d"
    #fields
    puts "field_name   :CA_PARITY_ERROR "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AREFRESH "
    puts "field_access :WR "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AREF_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AREF_SW_ACK "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x6d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x6d $data
}

proc mc_0x6d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x6d]

    return $rdata
}

proc mc_CA_PARITY_ERROR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6d 0 1 $data 
} 
 
proc mc_CA_PARITY_ERROR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6d 0 1 ] 

    return $rdata 
}

proc mc_AREFRESH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6d 8 1 $data 
} 
 
proc mc_AREFRESH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6d 8 1 ] 

    return $rdata 
}

proc mc_AREF_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6d 16 1 $data 
} 
 
proc mc_AREF_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6d 16 1 ] 

    return $rdata 
}

proc mc_AREF_SW_ACK_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6d 24 1 $data 
} 
 
proc mc_AREF_SW_ACK_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6d 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x6e_print {} {
    puts "addr: 0x6e"
    #fields
    puts "field_name   :TREF_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :TRFC_OPT_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x3 "
    puts "field_name   :CS_COMPARISON_FOR_REFRESH_DEPTH "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x10 "
} 

proc mc_0x6e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x6e $data
}

proc mc_0x6e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x6e]

    return $rdata
}

proc mc_TREF_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6e 0 1 $data 
} 
 
proc mc_TREF_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6e 0 1 ] 

    return $rdata 
}

proc mc_TRFC_OPT_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6e 8 3 $data 
} 
 
proc mc_TRFC_OPT_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6e 8 3 ] 

    return $rdata 
}

proc mc_CS_COMPARISON_FOR_REFRESH_DEPTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6e 16 5 $data 
} 
 
proc mc_CS_COMPARISON_FOR_REFRESH_DEPTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6e 16 5 ] 

    return $rdata 
}

#################################

proc mc_0x6f_print {} {
    puts "addr: 0x6f"
    #fields
    puts "field_name   :TRFC_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x33b "
} 

proc mc_0x6f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x6f $data
}

proc mc_0x6f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x6f]

    return $rdata
}

proc mc_TRFC_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x6f 0 10 $data 
} 
 
proc mc_TRFC_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x6f 0 10 ] 

    return $rdata 
}

#################################

proc mc_0x70_print {} {
    puts "addr: 0x70"
    #fields
    puts "field_name   :TREF_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :20 "
    puts "default field_value  :0x2aa4 "
} 

proc mc_0x70_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x70 $data
}

proc mc_0x70_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x70]

    return $rdata
}

proc mc_TREF_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x70 0 20 $data 
} 
 
proc mc_TREF_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x70 0 20 ] 

    return $rdata 
}

#################################

proc mc_0x71_print {} {
    puts "addr: 0x71"
    #fields
    puts "field_name   :TRFC_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x33b "
} 

proc mc_0x71_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x71 $data
}

proc mc_0x71_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x71]

    return $rdata
}

proc mc_TRFC_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x71 0 10 $data 
} 
 
proc mc_TRFC_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x71 0 10 ] 

    return $rdata 
}

#################################

proc mc_0x72_print {} {
    puts "addr: 0x72"
    #fields
    puts "field_name   :TREF_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :20 "
    puts "default field_value  :0x2aa4 "
} 

proc mc_0x72_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x72 $data
}

proc mc_0x72_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x72]

    return $rdata
}

proc mc_TREF_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x72 0 20 $data 
} 
 
proc mc_TREF_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x72 0 20 ] 

    return $rdata 
}

#################################

proc mc_0x73_print {} {
    puts "addr: 0x73"
    #fields
    puts "field_name   :TREF_INTERVAL "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :20 "
    puts "default field_value  :0x5 "
} 

proc mc_0x73_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x73 $data
}

proc mc_0x73_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x73]

    return $rdata
}

proc mc_TREF_INTERVAL_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x73 0 20 $data 
} 
 
proc mc_TREF_INTERVAL_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x73 0 20 ] 

    return $rdata 
}

#################################

proc mc_0x74_print {} {
    puts "addr: 0x74"
    #fields
    puts "field_name   :TRFM_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x33b "
    puts "field_name   :TRFM_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :10 "
    puts "default field_value  :0x33b "
} 

proc mc_0x74_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x74 $data
}

proc mc_0x74_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x74]

    return $rdata
}

proc mc_TRFM_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x74 0 10 $data 
} 
 
proc mc_TRFM_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x74 0 10 ] 

    return $rdata 
}

proc mc_TRFM_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x74 16 10 $data 
} 
 
proc mc_TRFM_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x74 16 10 ] 

    return $rdata 
}

#################################

proc mc_0x75_print {} {
    puts "addr: 0x75"
    #fields
    puts "field_name   :TRFM_SB_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :TRFM2ACT_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
} 

proc mc_0x75_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x75 $data
}

proc mc_0x75_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x75]

    return $rdata
}

proc mc_TRFM_SB_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x75 0 10 $data 
} 
 
proc mc_TRFM_SB_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x75 0 10 ] 

    return $rdata 
}

proc mc_TRFM2ACT_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x75 16 8 $data 
} 
 
proc mc_TRFM2ACT_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x75 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x76_print {} {
    puts "addr: 0x76"
    #fields
    puts "field_name   :TRFM_SB_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :TRFM2ACT_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
} 

proc mc_0x76_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x76 $data
}

proc mc_0x76_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x76]

    return $rdata
}

proc mc_TRFM_SB_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x76 0 10 $data 
} 
 
proc mc_TRFM_SB_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x76 0 10 ] 

    return $rdata 
}

proc mc_TRFM2ACT_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x76 16 8 $data 
} 
 
proc mc_TRFM2ACT_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x76 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x77_print {} {
    puts "addr: 0x77"
    #fields
    puts "field_name   :TRFM_SB_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :TRFM2ACT_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
} 

proc mc_0x77_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x77 $data
}

proc mc_0x77_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x77]

    return $rdata
}

proc mc_TRFM_SB_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x77 0 10 $data 
} 
 
proc mc_TRFM_SB_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x77 0 10 ] 

    return $rdata 
}

proc mc_TRFM2ACT_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x77 16 8 $data 
} 
 
proc mc_TRFM2ACT_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x77 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x78_print {} {
    puts "addr: 0x78"
    #fields
    puts "field_name   :TRFM_SB_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :TRFM2ACT_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
    puts "field_name   :RFM_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x78_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x78 $data
}

proc mc_0x78_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x78]

    return $rdata
}

proc mc_TRFM_SB_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x78 0 10 $data 
} 
 
proc mc_TRFM_SB_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x78 0 10 ] 

    return $rdata 
}

proc mc_TRFM2ACT_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x78 16 8 $data 
} 
 
proc mc_TRFM2ACT_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x78 16 8 ] 

    return $rdata 
}

proc mc_RFM_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x78 24 1 $data 
} 
 
proc mc_RFM_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x78 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x79_print {} {
    puts "addr: 0x79"
    #fields
    puts "field_name   :REF_RFM_PRIO "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :RAA_CNT_DECR_PER_REF "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :10 "
    puts "default field_value  :0x20 "
} 

proc mc_0x79_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x79 $data
}

proc mc_0x79_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x79]

    return $rdata
}

proc mc_REF_RFM_PRIO_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x79 0 1 $data 
} 
 
proc mc_REF_RFM_PRIO_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x79 0 1 ] 

    return $rdata 
}

proc mc_RAA_CNT_DECR_PER_REF_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x79 8 10 $data 
} 
 
proc mc_RAA_CNT_DECR_PER_REF_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x79 8 10 ] 

    return $rdata 
}

#################################

proc mc_0x7a_print {} {
    puts "addr: 0x7a"
    #fields
    puts "field_name   :RAAIMT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x20 "
    puts "field_name   :RAAMMT "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :10 "
    puts "default field_value  :0x5f "
} 

proc mc_0x7a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x7a $data
}

proc mc_0x7a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x7a]

    return $rdata
}

proc mc_RAAIMT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7a 0 10 $data 
} 
 
proc mc_RAAIMT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7a 0 10 ] 

    return $rdata 
}

proc mc_RAAMMT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7a 16 10 $data 
} 
 
proc mc_RAAMMT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7a 16 10 ] 

    return $rdata 
}

#################################

proc mc_0x7b_print {} {
    puts "addr: 0x7b"
    #fields
    puts "field_name   :RFM_SB_CONT_EN_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x0 "
    puts "field_name   :RFM_NORM_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :10 "
    puts "default field_value  :0x40 "
} 

proc mc_0x7b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x7b $data
}

proc mc_0x7b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x7b]

    return $rdata
}

proc mc_RFM_SB_CONT_EN_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7b 0 10 $data 
} 
 
proc mc_RFM_SB_CONT_EN_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7b 0 10 ] 

    return $rdata 
}

proc mc_RFM_NORM_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7b 16 10 $data 
} 
 
proc mc_RFM_NORM_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7b 16 10 ] 

    return $rdata 
}

#################################

proc mc_0x7c_print {} {
    puts "addr: 0x7c"
    #fields
    puts "field_name   :RFM_HIGH_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x5b "
    puts "field_name   :TRFC_PB_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
} 

proc mc_0x7c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x7c $data
}

proc mc_0x7c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x7c]

    return $rdata
}

proc mc_RFM_HIGH_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7c 0 10 $data 
} 
 
proc mc_RFM_HIGH_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7c 0 10 ] 

    return $rdata 
}

proc mc_TRFC_PB_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7c 16 10 $data 
} 
 
proc mc_TRFC_PB_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7c 16 10 ] 

    return $rdata 
}

#################################

proc mc_0x7d_print {} {
    puts "addr: 0x7d"
    #fields
    puts "field_name   :TPBR2ACT_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
    puts "field_name   :TPBR2PBR_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
} 

proc mc_0x7d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x7d $data
}

proc mc_0x7d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x7d]

    return $rdata
}

proc mc_TPBR2ACT_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7d 0 8 $data 
} 
 
proc mc_TPBR2ACT_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7d 0 8 ] 

    return $rdata 
}

proc mc_TPBR2PBR_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7d 8 10 $data 
} 
 
proc mc_TPBR2PBR_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7d 8 10 ] 

    return $rdata 
}

#################################

proc mc_0x7e_print {} {
    puts "addr: 0x7e"
    #fields
    puts "field_name   :TRFC_PB_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :TPBR2ACT_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
} 

proc mc_0x7e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x7e $data
}

proc mc_0x7e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x7e]

    return $rdata
}

proc mc_TRFC_PB_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7e 0 10 $data 
} 
 
proc mc_TRFC_PB_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7e 0 10 ] 

    return $rdata 
}

proc mc_TPBR2ACT_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7e 16 8 $data 
} 
 
proc mc_TPBR2ACT_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7e 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x7f_print {} {
    puts "addr: 0x7f"
    #fields
    puts "field_name   :TPBR2PBR_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :TRFC_PB_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
} 

proc mc_0x7f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x7f $data
}

proc mc_0x7f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x7f]

    return $rdata
}

proc mc_TPBR2PBR_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7f 0 10 $data 
} 
 
proc mc_TPBR2PBR_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7f 0 10 ] 

    return $rdata 
}

proc mc_TRFC_PB_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x7f 16 10 $data 
} 
 
proc mc_TRFC_PB_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x7f 16 10 ] 

    return $rdata 
}

#################################

proc mc_0x80_print {} {
    puts "addr: 0x80"
    #fields
    puts "field_name   :TPBR2ACT_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
    puts "field_name   :TPBR2PBR_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
} 

proc mc_0x80_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x80 $data
}

proc mc_0x80_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x80]

    return $rdata
}

proc mc_TPBR2ACT_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x80 0 8 $data 
} 
 
proc mc_TPBR2ACT_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x80 0 8 ] 

    return $rdata 
}

proc mc_TPBR2PBR_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x80 8 10 $data 
} 
 
proc mc_TPBR2PBR_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x80 8 10 ] 

    return $rdata 
}

#################################

proc mc_0x81_print {} {
    puts "addr: 0x81"
    #fields
    puts "field_name   :TRFC_PB_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :TPBR2ACT_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x55 "
} 

proc mc_0x81_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x81 $data
}

proc mc_0x81_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x81]

    return $rdata
}

proc mc_TRFC_PB_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x81 0 10 $data 
} 
 
proc mc_TRFC_PB_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x81 0 10 ] 

    return $rdata 
}

proc mc_TPBR2ACT_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x81 16 8 $data 
} 
 
proc mc_TPBR2ACT_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x81 16 8 ] 

    return $rdata 
}

#################################

proc mc_0x82_print {} {
    puts "addr: 0x82"
    #fields
    puts "field_name   :TPBR2PBR_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x16d "
    puts "field_name   :PBR_MODE_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :SELECT_BANK_IN_Q "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x82_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x82 $data
}

proc mc_0x82_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x82]

    return $rdata
}

proc mc_TPBR2PBR_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x82 0 10 $data 
} 
 
proc mc_TPBR2PBR_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x82 0 10 ] 

    return $rdata 
}

proc mc_PBR_MODE_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x82 16 4 $data 
} 
 
proc mc_PBR_MODE_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x82 16 4 ] 

    return $rdata 
}

proc mc_SELECT_BANK_IN_Q_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x82 24 1 $data 
} 
 
proc mc_SELECT_BANK_IN_Q_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x82 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x83_print {} {
    puts "addr: 0x83"
    #fields
    puts "field_name   :PBR_NUMERIC_ORDER "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :PBR_CONT_REQ_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :AREF_PBR_CONT_EN_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x11 "
} 

proc mc_0x83_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x83 $data
}

proc mc_0x83_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x83]

    return $rdata
}

proc mc_PBR_NUMERIC_ORDER_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x83 0 1 $data 
} 
 
proc mc_PBR_NUMERIC_ORDER_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x83 0 1 ] 

    return $rdata 
}

proc mc_PBR_CONT_REQ_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x83 8 1 $data 
} 
 
proc mc_PBR_CONT_REQ_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x83 8 1 ] 

    return $rdata 
}

proc mc_AREF_PBR_CONT_EN_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x83 16 5 $data 
} 
 
proc mc_AREF_PBR_CONT_EN_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x83 16 5 ] 

    return $rdata 
}

#################################

proc mc_0x84_print {} {
    puts "addr: 0x84"
    #fields
    puts "field_name   :TPDEX_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x16 "
    puts "field_name   :TPDEX_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x16 "
} 

proc mc_0x84_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x84 $data
}

proc mc_0x84_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x84]

    return $rdata
}

proc mc_TPDEX_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x84 0 16 $data 
} 
 
proc mc_TPDEX_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x84 0 16 ] 

    return $rdata 
}

proc mc_TPDEX_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x84 16 16 $data 
} 
 
proc mc_TPDEX_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x84 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x85_print {} {
    puts "addr: 0x85"
    #fields
    puts "field_name   :TXSR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x700 "
    puts "field_name   :TXSNR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x33b "
} 

proc mc_0x85_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x85 $data
}

proc mc_0x85_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x85]

    return $rdata
}

proc mc_TXSR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x85 0 16 $data 
} 
 
proc mc_TXSR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x85 0 16 ] 

    return $rdata 
}

proc mc_TXSNR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x85 16 16 $data 
} 
 
proc mc_TXSNR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x85 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x86_print {} {
    puts "addr: 0x86"
    #fields
    puts "field_name   :TCPDED_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0xf "
    puts "field_name   :TXSR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x700 "
} 

proc mc_0x86_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x86 $data
}

proc mc_0x86_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x86]

    return $rdata
}

proc mc_TCPDED_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x86 0 8 $data 
} 
 
proc mc_TCPDED_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x86 0 8 ] 

    return $rdata 
}

proc mc_TXSR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x86 8 16 $data 
} 
 
proc mc_TXSR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x86 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x87_print {} {
    puts "addr: 0x87"
    #fields
    puts "field_name   :TXSNR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x33b "
    puts "field_name   :TCPDED_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0xf "
    puts "field_name   :SRX_NOP_CMDS "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x5 "
} 

proc mc_0x87_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x87 $data
}

proc mc_0x87_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x87]

    return $rdata
}

proc mc_TXSNR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x87 0 16 $data 
} 
 
proc mc_TXSNR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x87 0 16 ] 

    return $rdata 
}

proc mc_TCPDED_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x87 16 8 $data 
} 
 
proc mc_TCPDED_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x87 16 8 ] 

    return $rdata 
}

proc mc_SRX_NOP_CMDS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x87 24 4 $data 
} 
 
proc mc_SRX_NOP_CMDS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x87 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x88_print {} {
    puts "addr: 0x88"
    #fields
    puts "field_name   :TCMDCKE_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :TCMDCKE_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :PWRUP_SREFRESH_EXIT "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :SREFRESH_EXIT_NO_REFRESH "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x88_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x88 $data
}

proc mc_0x88_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x88]

    return $rdata
}

proc mc_TCMDCKE_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x88 0 4 $data 
} 
 
proc mc_TCMDCKE_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x88 0 4 ] 

    return $rdata 
}

proc mc_TCMDCKE_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x88 8 4 $data 
} 
 
proc mc_TCMDCKE_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x88 8 4 ] 

    return $rdata 
}

proc mc_PWRUP_SREFRESH_EXIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x88 16 1 $data 
} 
 
proc mc_PWRUP_SREFRESH_EXIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x88 16 1 ] 

    return $rdata 
}

proc mc_SREFRESH_EXIT_NO_REFRESH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x88 24 1 $data 
} 
 
proc mc_SREFRESH_EXIT_NO_REFRESH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x88 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x89_print {} {
    puts "addr: 0x89"
    #fields
    puts "field_name   :ENABLE_QUICK_SREFRESH "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :CKE_DELAY "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x3 "
    puts "field_name   :RESERVED "
    puts "field_access :RW+ "
    puts "field_bitpos :24 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0x89_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x89 $data
}

proc mc_0x89_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x89]

    return $rdata
}

proc mc_ENABLE_QUICK_SREFRESH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x89 0 1 $data 
} 
 
proc mc_ENABLE_QUICK_SREFRESH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x89 0 1 ] 

    return $rdata 
}

proc mc_CKE_DELAY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x89 8 3 $data 
} 
 
proc mc_CKE_DELAY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x89 8 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x89 24 7 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x89 24 7 ] 

    return $rdata 
}

#################################

proc mc_0x8a_print {} {
    puts "addr: 0x8a"
    #fields
    puts "field_name   :DFI_FREQ_CHANGE_STATE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :DFS_ZQ_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x8a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x8a $data
}

proc mc_0x8a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x8a]

    return $rdata
}

proc mc_DFI_FREQ_CHANGE_STATE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8a 0 1 $data 
} 
 
proc mc_DFI_FREQ_CHANGE_STATE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8a 0 1 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8a 8 1 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8a 8 1 ] 

    return $rdata 
}

proc mc_DFS_ZQ_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8a 16 1 $data 
} 
 
proc mc_DFS_ZQ_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8a 16 1 ] 

    return $rdata 
}

#################################

proc mc_0x8b_print {} {
    puts "addr: 0x8b"
    #fields
    puts "field_name   :POST_DFS_WAIT_TIME_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x8b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x8b $data
}

proc mc_0x8b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x8b]

    return $rdata
}

proc mc_POST_DFS_WAIT_TIME_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8b 16 16 $data 
} 
 
proc mc_POST_DFS_WAIT_TIME_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8b 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x8c_print {} {
    puts "addr: 0x8c"
    #fields
    puts "field_name   :POST_DFS_WAIT_TIME_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x8c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x8c $data
}

proc mc_0x8c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x8c]

    return $rdata
}

proc mc_POST_DFS_WAIT_TIME_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8c 16 16 $data 
} 
 
proc mc_POST_DFS_WAIT_TIME_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8c 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x8d_print {} {
    puts "addr: 0x8d"
    #fields
    puts "field_name   :ZQ_STATUS_LOG "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x40 "
} 

proc mc_0x8d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x8d $data
}

proc mc_0x8d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x8d]

    return $rdata
}

proc mc_ZQ_STATUS_LOG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8d 0 3 $data 
} 
 
proc mc_ZQ_STATUS_LOG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8d 0 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8d 8 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8d 8 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8d 16 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8d 16 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8d 24 8 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8d 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x8e_print {} {
    puts "addr: 0x8e"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x10 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x80 "
    puts "field_name   :UPD_CTRLUPD_NORM_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x3 "
} 

proc mc_0x8e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x8e $data
}

proc mc_0x8e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x8e]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8e 0 8 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8e 0 8 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8e 8 8 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8e 8 8 ] 

    return $rdata 
}

proc mc_UPD_CTRLUPD_NORM_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8e 16 16 $data 
} 
 
proc mc_UPD_CTRLUPD_NORM_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8e 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x8f_print {} {
    puts "addr: 0x8f"
    #fields
    puts "field_name   :UPD_CTRLUPD_HIGH_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x4 "
    puts "field_name   :UPD_CTRLUPD_TIMEOUT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x5 "
} 

proc mc_0x8f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x8f $data
}

proc mc_0x8f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x8f]

    return $rdata
}

proc mc_UPD_CTRLUPD_HIGH_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8f 0 16 $data 
} 
 
proc mc_UPD_CTRLUPD_HIGH_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8f 0 16 ] 

    return $rdata 
}

proc mc_UPD_CTRLUPD_TIMEOUT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x8f 16 16 $data 
} 
 
proc mc_UPD_CTRLUPD_TIMEOUT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x8f 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x90_print {} {
    puts "addr: 0x90"
    #fields
    puts "field_name   :UPD_CTRLUPD_SW_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x4 "
    puts "field_name   :UPD_PHYUPD_DFI_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x90_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x90 $data
}

proc mc_0x90_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x90]

    return $rdata
}

proc mc_UPD_CTRLUPD_SW_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x90 0 16 $data 
} 
 
proc mc_UPD_CTRLUPD_SW_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x90 0 16 ] 

    return $rdata 
}

proc mc_UPD_PHYUPD_DFI_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x90 16 16 $data 
} 
 
proc mc_UPD_PHYUPD_DFI_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x90 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x91_print {} {
    puts "addr: 0x91"
    #fields
    puts "field_name   :UPD_CTRLUPD_NORM_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x3 "
    puts "field_name   :UPD_CTRLUPD_HIGH_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x4 "
} 

proc mc_0x91_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x91 $data
}

proc mc_0x91_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x91]

    return $rdata
}

proc mc_UPD_CTRLUPD_NORM_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x91 0 16 $data 
} 
 
proc mc_UPD_CTRLUPD_NORM_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x91 0 16 ] 

    return $rdata 
}

proc mc_UPD_CTRLUPD_HIGH_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x91 16 16 $data 
} 
 
proc mc_UPD_CTRLUPD_HIGH_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x91 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x92_print {} {
    puts "addr: 0x92"
    #fields
    puts "field_name   :UPD_CTRLUPD_TIMEOUT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x5 "
    puts "field_name   :UPD_CTRLUPD_SW_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x4 "
} 

proc mc_0x92_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x92 $data
}

proc mc_0x92_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x92]

    return $rdata
}

proc mc_UPD_CTRLUPD_TIMEOUT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x92 0 16 $data 
} 
 
proc mc_UPD_CTRLUPD_TIMEOUT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x92 0 16 ] 

    return $rdata 
}

proc mc_UPD_CTRLUPD_SW_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x92 16 16 $data 
} 
 
proc mc_UPD_CTRLUPD_SW_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x92 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x93_print {} {
    puts "addr: 0x93"
    #fields
    puts "field_name   :UPD_PHYUPD_DFI_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x93_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x93 $data
}

proc mc_0x93_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x93]

    return $rdata
}

proc mc_UPD_PHYUPD_DFI_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x93 0 16 $data 
} 
 
proc mc_UPD_PHYUPD_DFI_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x93 0 16 ] 

    return $rdata 
}

#################################

proc mc_0x94_print {} {
    puts "addr: 0x94"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x94_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x94 $data
}

proc mc_0x94_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x94]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x94 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x94 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x95_print {} {
    puts "addr: 0x95"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE0_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x95_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x95 $data
}

proc mc_0x95_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x95]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE0_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x95 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE0_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x95 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x96_print {} {
    puts "addr: 0x96"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE1_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x96_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x96 $data
}

proc mc_0x96_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x96]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE1_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x96 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE1_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x96 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x97_print {} {
    puts "addr: 0x97"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE2_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x97_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x97 $data
}

proc mc_0x97_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x97]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE2_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x97 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE2_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x97 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x98_print {} {
    puts "addr: 0x98"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE3_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x98_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x98 $data
}

proc mc_0x98_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x98]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE3_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x98 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE3_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x98 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x99_print {} {
    puts "addr: 0x99"
    #fields
    puts "field_name   :PHYMSTR_DFI4_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x99_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x99 $data
}

proc mc_0x99_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x99]

    return $rdata
}

proc mc_PHYMSTR_DFI4_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x99 0 16 $data 
} 
 
proc mc_PHYMSTR_DFI4_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x99 0 16 ] 

    return $rdata 
}

#################################

proc mc_0x9a_print {} {
    puts "addr: 0x9a"
    #fields
    puts "field_name   :TDFI_PHYMSTR_RESP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :20 "
    puts "default field_value  :0x12a7e "
} 

proc mc_0x9a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x9a $data
}

proc mc_0x9a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x9a]

    return $rdata
}

proc mc_TDFI_PHYMSTR_RESP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x9a 0 20 $data 
} 
 
proc mc_TDFI_PHYMSTR_RESP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x9a 0 20 ] 

    return $rdata 
}

#################################

proc mc_0x9b_print {} {
    puts "addr: 0x9b"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x9b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x9b $data
}

proc mc_0x9b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x9b]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x9b 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x9b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x9c_print {} {
    puts "addr: 0x9c"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE0_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x9c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x9c $data
}

proc mc_0x9c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x9c]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE0_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x9c 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE0_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x9c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x9d_print {} {
    puts "addr: 0x9d"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE1_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x9d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x9d $data
}

proc mc_0x9d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x9d]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE1_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x9d 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE1_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x9d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x9e_print {} {
    puts "addr: 0x9e"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE2_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x9e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x9e $data
}

proc mc_0x9e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x9e]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE2_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x9e 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE2_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x9e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x9f_print {} {
    puts "addr: 0x9f"
    #fields
    puts "field_name   :TDFI_PHYMSTR_MAX_TYPE3_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0xaa900 "
} 

proc mc_0x9f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x9f $data
}

proc mc_0x9f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x9f]

    return $rdata
}

proc mc_TDFI_PHYMSTR_MAX_TYPE3_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x9f 0 32 $data 
} 
 
proc mc_TDFI_PHYMSTR_MAX_TYPE3_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x9f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xa0_print {} {
    puts "addr: 0xa0"
    #fields
    puts "field_name   :PHYMSTR_DFI4_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa0 $data
}

proc mc_0xa0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa0]

    return $rdata
}

proc mc_PHYMSTR_DFI4_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa0 0 16 $data 
} 
 
proc mc_PHYMSTR_DFI4_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa0 0 16 ] 

    return $rdata 
}

#################################

proc mc_0xa1_print {} {
    puts "addr: 0xa1"
    #fields
    puts "field_name   :TDFI_PHYMSTR_RESP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :20 "
    puts "default field_value  :0x12a7e "
    puts "field_name   :PHYMSTR_NO_AREF "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa1 $data
}

proc mc_0xa1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa1]

    return $rdata
}

proc mc_TDFI_PHYMSTR_RESP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa1 0 20 $data 
} 
 
proc mc_TDFI_PHYMSTR_RESP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa1 0 20 ] 

    return $rdata 
}

proc mc_PHYMSTR_NO_AREF_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa1 24 1 $data 
} 
 
proc mc_PHYMSTR_NO_AREF_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa1 24 1 ] 

    return $rdata 
}

#################################

proc mc_0xa2_print {} {
    puts "addr: 0xa2"
    #fields
    puts "field_name   :PHYMSTR_ERROR_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :PHYMSTR_DFI_VERSION_4P0V1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :PHYMSTR_TRAIN_AFTER_INIT_COMPLETE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa2 $data
}

proc mc_0xa2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa2]

    return $rdata
}

proc mc_PHYMSTR_ERROR_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa2 0 2 $data 
} 
 
proc mc_PHYMSTR_ERROR_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa2 0 2 ] 

    return $rdata 
}

proc mc_PHYMSTR_DFI_VERSION_4P0V1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa2 8 1 $data 
} 
 
proc mc_PHYMSTR_DFI_VERSION_4P0V1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa2 8 1 ] 

    return $rdata 
}

proc mc_PHYMSTR_TRAIN_AFTER_INIT_COMPLETE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa2 16 1 $data 
} 
 
proc mc_PHYMSTR_TRAIN_AFTER_INIT_COMPLETE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa2 16 1 ] 

    return $rdata 
}

#################################

proc mc_0xa3_print {} {
    puts "addr: 0xa3"
    #fields
    puts "field_name   :MRR_TEMPCHK_NORM_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa3 $data
}

proc mc_0xa3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa3]

    return $rdata
}

proc mc_MRR_TEMPCHK_NORM_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa3 0 24 $data 
} 
 
proc mc_MRR_TEMPCHK_NORM_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa3 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xa4_print {} {
    puts "addr: 0xa4"
    #fields
    puts "field_name   :MRR_TEMPCHK_HIGH_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa4 $data
}

proc mc_0xa4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa4]

    return $rdata
}

proc mc_MRR_TEMPCHK_HIGH_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa4 0 24 $data 
} 
 
proc mc_MRR_TEMPCHK_HIGH_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa4 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xa5_print {} {
    puts "addr: 0xa5"
    #fields
    puts "field_name   :MRR_TEMPCHK_TIMEOUT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa5 $data
}

proc mc_0xa5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa5]

    return $rdata
}

proc mc_MRR_TEMPCHK_TIMEOUT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa5 0 24 $data 
} 
 
proc mc_MRR_TEMPCHK_TIMEOUT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa5 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xa6_print {} {
    puts "addr: 0xa6"
    #fields
    puts "field_name   :MRR_TEMPCHK_NORM_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa6 $data
}

proc mc_0xa6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa6]

    return $rdata
}

proc mc_MRR_TEMPCHK_NORM_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa6 0 24 $data 
} 
 
proc mc_MRR_TEMPCHK_NORM_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa6 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xa7_print {} {
    puts "addr: 0xa7"
    #fields
    puts "field_name   :MRR_TEMPCHK_HIGH_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa7 $data
}

proc mc_0xa7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa7]

    return $rdata
}

proc mc_MRR_TEMPCHK_HIGH_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa7 0 24 $data 
} 
 
proc mc_MRR_TEMPCHK_HIGH_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa7 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xa8_print {} {
    puts "addr: 0xa8"
    #fields
    puts "field_name   :MRR_TEMPCHK_TIMEOUT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
    puts "field_name   :PPR_COMMAND_MRR_REGNUM "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa8 $data
}

proc mc_0xa8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa8]

    return $rdata
}

proc mc_MRR_TEMPCHK_TIMEOUT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa8 0 24 $data 
} 
 
proc mc_MRR_TEMPCHK_TIMEOUT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa8 0 24 ] 

    return $rdata 
}

proc mc_PPR_COMMAND_MRR_REGNUM_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa8 24 8 $data 
} 
 
proc mc_PPR_COMMAND_MRR_REGNUM_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa8 24 8 ] 

    return $rdata 
}

#################################

proc mc_0xa9_print {} {
    puts "addr: 0xa9"
    #fields
    puts "field_name   :PPR_CONTROL "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :PPR_COMMAND "
    puts "field_access :WR "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
    puts "field_name   :PPR_COMMAND_MRW_REGNUM "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0xa9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xa9 $data
}

proc mc_0xa9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xa9]

    return $rdata
}

proc mc_PPR_CONTROL_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa9 0 1 $data 
} 
 
proc mc_PPR_CONTROL_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa9 0 1 ] 

    return $rdata 
}

proc mc_PPR_COMMAND_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa9 8 3 $data 
} 
 
proc mc_PPR_COMMAND_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa9 8 3 ] 

    return $rdata 
}

proc mc_PPR_COMMAND_MRW_REGNUM_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xa9 16 8 $data 
} 
 
proc mc_PPR_COMMAND_MRW_REGNUM_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xa9 16 8 ] 

    return $rdata 
}

#################################

proc mc_0xaa_print {} {
    puts "addr: 0xaa"
    #fields
    puts "field_name   :PPR_COMMAND_MRW_DATA "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xaa_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xaa $data
}

proc mc_0xaa_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xaa]

    return $rdata
}

proc mc_PPR_COMMAND_MRW_DATA_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xaa 0 18 $data 
} 
 
proc mc_PPR_COMMAND_MRW_DATA_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xaa 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xab_print {} {
    puts "addr: 0xab"
    #fields
    puts "field_name   :PPR_ROW_ADDRESS "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
    puts "field_name   :PPR_BANK_ADDRESS "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
} 

proc mc_0xab_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xab $data
}

proc mc_0xab_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xab]

    return $rdata
}

proc mc_PPR_ROW_ADDRESS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xab 0 18 $data 
} 
 
proc mc_PPR_ROW_ADDRESS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xab 0 18 ] 

    return $rdata 
}

proc mc_PPR_BANK_ADDRESS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xab 24 5 $data 
} 
 
proc mc_PPR_BANK_ADDRESS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xab 24 5 ] 

    return $rdata 
}

#################################

proc mc_0xac_print {} {
    puts "addr: 0xac"
    #fields
    puts "field_name   :PPR_CS_ADDRESS "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xac_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xac $data
}

proc mc_0xac_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xac]

    return $rdata
}

proc mc_PPR_CS_ADDRESS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xac 0 1 $data 
} 
 
proc mc_PPR_CS_ADDRESS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xac 0 1 ] 

    return $rdata 
}

#################################

proc mc_0xb6_print {} {
    puts "addr: 0xb6"
    #fields
    puts "field_name   :PPR_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :POST_INIT_SW_MODE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :DFI_BOOT_STATE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :FM_OVRIDE_CONTROL "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xb6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xb6 $data
}

proc mc_0xb6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xb6]

    return $rdata
}

proc mc_PPR_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb6 0 2 $data 
} 
 
proc mc_PPR_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb6 0 2 ] 

    return $rdata 
}

proc mc_POST_INIT_SW_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb6 8 1 $data 
} 
 
proc mc_POST_INIT_SW_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb6 8 1 ] 

    return $rdata 
}

proc mc_DFI_BOOT_STATE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb6 16 1 $data 
} 
 
proc mc_DFI_BOOT_STATE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb6 16 1 ] 

    return $rdata 
}

proc mc_FM_OVRIDE_CONTROL_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb6 24 1 $data 
} 
 
proc mc_FM_OVRIDE_CONTROL_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb6 24 1 ] 

    return $rdata 
}

#################################

proc mc_0xb7_print {} {
    puts "addr: 0xb7"
    #fields
    puts "field_name   :CKSRE_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x10 "
    puts "field_name   :CKSRX_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x25 "
    puts "field_name   :CKSRE_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x10 "
    puts "field_name   :CKSRX_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x25 "
} 

proc mc_0xb7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xb7 $data
}

proc mc_0xb7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xb7]

    return $rdata
}

proc mc_CKSRE_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb7 0 8 $data 
} 
 
proc mc_CKSRE_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb7 0 8 ] 

    return $rdata 
}

proc mc_CKSRX_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb7 8 8 $data 
} 
 
proc mc_CKSRX_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb7 8 8 ] 

    return $rdata 
}

proc mc_CKSRE_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb7 16 8 $data 
} 
 
proc mc_CKSRE_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb7 16 8 ] 

    return $rdata 
}

proc mc_CKSRX_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb7 24 8 $data 
} 
 
proc mc_CKSRX_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb7 24 8 ] 

    return $rdata 
}

#################################

proc mc_0xb8_print {} {
    puts "addr: 0xb8"
    #fields
    puts "field_name   :LOWPOWER_REFRESH_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :LP_CMD "
    puts "field_access :WR "
    puts "field_bitpos :8 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPI_IDLE_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :6 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPI_CTRL_IDLE_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0x0 "
} 

proc mc_0xb8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xb8 $data
}

proc mc_0xb8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xb8]

    return $rdata
}

proc mc_LOWPOWER_REFRESH_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb8 0 2 $data 
} 
 
proc mc_LOWPOWER_REFRESH_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb8 0 2 ] 

    return $rdata 
}

proc mc_LP_CMD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb8 8 7 $data 
} 
 
proc mc_LP_CMD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb8 8 7 ] 

    return $rdata 
}

proc mc_LPI_IDLE_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb8 16 6 $data 
} 
 
proc mc_LPI_IDLE_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb8 16 6 ] 

    return $rdata 
}

proc mc_LPI_CTRL_IDLE_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb8 24 6 $data 
} 
 
proc mc_LPI_CTRL_IDLE_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb8 24 6 ] 

    return $rdata 
}

#################################

proc mc_0xb9_print {} {
    puts "addr: 0xb9"
    #fields
    puts "field_name   :LPI_SR_SHORT_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :6 "
    puts "default field_value  :0x7 "
    puts "field_name   :LPI_SR_LONG_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :6 "
    puts "default field_value  :0x9 "
    puts "field_name   :LPI_CTRL_SR_LONG_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :6 "
    puts "default field_value  :0x9 "
    puts "field_name   :LPI_SR_LONG_MCCLK_GATE_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0xa "
} 

proc mc_0xb9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xb9 $data
}

proc mc_0xb9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xb9]

    return $rdata
}

proc mc_LPI_SR_SHORT_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb9 0 6 $data 
} 
 
proc mc_LPI_SR_SHORT_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb9 0 6 ] 

    return $rdata 
}

proc mc_LPI_SR_LONG_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb9 8 6 $data 
} 
 
proc mc_LPI_SR_LONG_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb9 8 6 ] 

    return $rdata 
}

proc mc_LPI_CTRL_SR_LONG_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb9 16 6 $data 
} 
 
proc mc_LPI_CTRL_SR_LONG_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb9 16 6 ] 

    return $rdata 
}

proc mc_LPI_SR_LONG_MCCLK_GATE_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xb9 24 6 $data 
} 
 
proc mc_LPI_SR_LONG_MCCLK_GATE_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xb9 24 6 ] 

    return $rdata 
}

#################################

proc mc_0xba_print {} {
    puts "addr: 0xba"
    #fields
    puts "field_name   :LPI_CTRL_SR_LONG_MCCLK_GATE_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :6 "
    puts "default field_value  :0xa "
    puts "field_name   :LPI_PD_WAKEUP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :6 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :6 "
    puts "default field_value  :0xe "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0xe "
} 

proc mc_0xba_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xba $data
}

proc mc_0xba_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xba]

    return $rdata
}

proc mc_LPI_CTRL_SR_LONG_MCCLK_GATE_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xba 0 6 $data 
} 
 
proc mc_LPI_CTRL_SR_LONG_MCCLK_GATE_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xba 0 6 ] 

    return $rdata 
}

proc mc_LPI_PD_WAKEUP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xba 8 6 $data 
} 
 
proc mc_LPI_PD_WAKEUP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xba 8 6 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xba 16 6 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xba 16 6 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xba 24 6 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xba 24 6 ] 

    return $rdata 
}

#################################

proc mc_0xbb_print {} {
    puts "addr: 0xbb"
    #fields
    puts "field_name   :LPI_IDLE_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :6 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPI_CTRL_IDLE_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :6 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPI_SR_SHORT_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :6 "
    puts "default field_value  :0x7 "
    puts "field_name   :LPI_SR_LONG_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0x9 "
} 

proc mc_0xbb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xbb $data
}

proc mc_0xbb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xbb]

    return $rdata
}

proc mc_LPI_IDLE_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbb 0 6 $data 
} 
 
proc mc_LPI_IDLE_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbb 0 6 ] 

    return $rdata 
}

proc mc_LPI_CTRL_IDLE_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbb 8 6 $data 
} 
 
proc mc_LPI_CTRL_IDLE_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbb 8 6 ] 

    return $rdata 
}

proc mc_LPI_SR_SHORT_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbb 16 6 $data 
} 
 
proc mc_LPI_SR_SHORT_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbb 16 6 ] 

    return $rdata 
}

proc mc_LPI_SR_LONG_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbb 24 6 $data 
} 
 
proc mc_LPI_SR_LONG_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbb 24 6 ] 

    return $rdata 
}

#################################

proc mc_0xbc_print {} {
    puts "addr: 0xbc"
    #fields
    puts "field_name   :LPI_CTRL_SR_LONG_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :6 "
    puts "default field_value  :0x9 "
    puts "field_name   :LPI_SR_LONG_MCCLK_GATE_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :6 "
    puts "default field_value  :0xa "
    puts "field_name   :LPI_CTRL_SR_LONG_MCCLK_GATE_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :6 "
    puts "default field_value  :0xa "
    puts "field_name   :LPI_PD_WAKEUP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0x1 "
} 

proc mc_0xbc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xbc $data
}

proc mc_0xbc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xbc]

    return $rdata
}

proc mc_LPI_CTRL_SR_LONG_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbc 0 6 $data 
} 
 
proc mc_LPI_CTRL_SR_LONG_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbc 0 6 ] 

    return $rdata 
}

proc mc_LPI_SR_LONG_MCCLK_GATE_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbc 8 6 $data 
} 
 
proc mc_LPI_SR_LONG_MCCLK_GATE_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbc 8 6 ] 

    return $rdata 
}

proc mc_LPI_CTRL_SR_LONG_MCCLK_GATE_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbc 16 6 $data 
} 
 
proc mc_LPI_CTRL_SR_LONG_MCCLK_GATE_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbc 16 6 ] 

    return $rdata 
}

proc mc_LPI_PD_WAKEUP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbc 24 6 $data 
} 
 
proc mc_LPI_PD_WAKEUP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbc 24 6 ] 

    return $rdata 
}

#################################

proc mc_0xbd_print {} {
    puts "addr: 0xbd"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :6 "
    puts "default field_value  :0xe "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :6 "
    puts "default field_value  :0xe "
    puts "field_name   :LPI_WAKEUP_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :6 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPI_CTRL_WAKEUP_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :6 "
    puts "default field_value  :0x2d "
} 

proc mc_0xbd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xbd $data
}

proc mc_0xbd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xbd]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbd 0 6 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbd 0 6 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbd 8 6 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbd 8 6 ] 

    return $rdata 
}

proc mc_LPI_WAKEUP_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbd 16 6 $data 
} 
 
proc mc_LPI_WAKEUP_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbd 16 6 ] 

    return $rdata 
}

proc mc_LPI_CTRL_WAKEUP_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbd 24 6 $data 
} 
 
proc mc_LPI_CTRL_WAKEUP_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbd 24 6 ] 

    return $rdata 
}

#################################

proc mc_0xbe_print {} {
    puts "addr: 0xbe"
    #fields
    puts "field_name   :LPI_CTRL_REQ_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPI_TIMER_COUNT "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :12 "
    puts "default field_value  :0x3 "
} 

proc mc_0xbe_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xbe $data
}

proc mc_0xbe_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xbe]

    return $rdata
}

proc mc_LPI_CTRL_REQ_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbe 0 1 $data 
} 
 
proc mc_LPI_CTRL_REQ_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbe 0 1 ] 

    return $rdata 
}

proc mc_LPI_TIMER_COUNT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbe 8 12 $data 
} 
 
proc mc_LPI_TIMER_COUNT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbe 8 12 ] 

    return $rdata 
}

#################################

proc mc_0xbf_print {} {
    puts "addr: 0xbf"
    #fields
    puts "field_name   :LPI_CTRL_TIMER_COUNT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0x3 "
    puts "field_name   :LPI_WAKEUP_TIMEOUT "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :12 "
    puts "default field_value  :0x4 "
} 

proc mc_0xbf_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xbf $data
}

proc mc_0xbf_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xbf]

    return $rdata
}

proc mc_LPI_CTRL_TIMER_COUNT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbf 0 12 $data 
} 
 
proc mc_LPI_CTRL_TIMER_COUNT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbf 0 12 ] 

    return $rdata 
}

proc mc_LPI_WAKEUP_TIMEOUT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xbf 16 12 $data 
} 
 
proc mc_LPI_WAKEUP_TIMEOUT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xbf 16 12 ] 

    return $rdata 
}

#################################

proc mc_0xc0_print {} {
    puts "addr: 0xc0"
    #fields
    puts "field_name   :LPI_CTRL_WAKEUP_TIMEOUT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0x4 "
    puts "field_name   :TDFI_LP_RESP "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0xa "
    puts "field_name   :LP_STATE "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc0 $data
}

proc mc_0xc0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc0]

    return $rdata
}

proc mc_LPI_CTRL_WAKEUP_TIMEOUT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc0 0 12 $data 
} 
 
proc mc_LPI_CTRL_WAKEUP_TIMEOUT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc0 0 12 ] 

    return $rdata 
}

proc mc_TDFI_LP_RESP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc0 16 5 $data 
} 
 
proc mc_TDFI_LP_RESP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc0 16 5 ] 

    return $rdata 
}

proc mc_LP_STATE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc0 24 7 $data 
} 
 
proc mc_LP_STATE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc0 24 7 ] 

    return $rdata 
}

#################################

proc mc_0xc1_print {} {
    puts "addr: 0xc1"
    #fields
    puts "field_name   :LP_AUTO_ENTRY_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :LP_AUTO_EXIT_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :LP_AUTO_MEM_GATE_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc1 $data
}

proc mc_0xc1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc1]

    return $rdata
}

proc mc_LP_AUTO_ENTRY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc1 0 4 $data 
} 
 
proc mc_LP_AUTO_ENTRY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc1 0 4 ] 

    return $rdata 
}

proc mc_LP_AUTO_EXIT_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc1 8 4 $data 
} 
 
proc mc_LP_AUTO_EXIT_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc1 8 4 ] 

    return $rdata 
}

proc mc_LP_AUTO_MEM_GATE_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc1 16 3 $data 
} 
 
proc mc_LP_AUTO_MEM_GATE_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc1 16 3 ] 

    return $rdata 
}

#################################

proc mc_0xc2_print {} {
    puts "addr: 0xc2"
    #fields
    puts "field_name   :LP_AUTO_PD_IDLE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0x0 "
    puts "field_name   :LP_AUTO_SR_SHORT_IDLE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :12 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc2 $data
}

proc mc_0xc2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc2]

    return $rdata
}

proc mc_LP_AUTO_PD_IDLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc2 0 12 $data 
} 
 
proc mc_LP_AUTO_PD_IDLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc2 0 12 ] 

    return $rdata 
}

proc mc_LP_AUTO_SR_SHORT_IDLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc2 16 12 $data 
} 
 
proc mc_LP_AUTO_SR_SHORT_IDLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc2 16 12 ] 

    return $rdata 
}

#################################

proc mc_0xc3_print {} {
    puts "addr: 0xc3"
    #fields
    puts "field_name   :LP_AUTO_SR_LONG_IDLE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :LP_AUTO_SR_LONG_MC_GATE_IDLE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :HW_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc3 $data
}

proc mc_0xc3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc3]

    return $rdata
}

proc mc_LP_AUTO_SR_LONG_IDLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc3 0 8 $data 
} 
 
proc mc_LP_AUTO_SR_LONG_IDLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc3 0 8 ] 

    return $rdata 
}

proc mc_LP_AUTO_SR_LONG_MC_GATE_IDLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc3 8 8 $data 
} 
 
proc mc_LP_AUTO_SR_LONG_MC_GATE_IDLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc3 8 8 ] 

    return $rdata 
}

proc mc_HW_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc3 16 16 $data 
} 
 
proc mc_HW_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc3 16 16 ] 

    return $rdata 
}

#################################

proc mc_0xc4_print {} {
    puts "addr: 0xc4"
    #fields
    puts "field_name   :HW_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPC_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc4 $data
}

proc mc_0xc4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc4]

    return $rdata
}

proc mc_HW_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc4 0 16 $data 
} 
 
proc mc_HW_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc4 0 16 ] 

    return $rdata 
}

proc mc_LPC_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc4 16 16 $data 
} 
 
proc mc_LPC_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc4 16 16 ] 

    return $rdata 
}

#################################

proc mc_0xc5_print {} {
    puts "addr: 0xc5"
    #fields
    puts "field_name   :LPC_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPC_SR_CTRLUPD_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPC_SR_PHYUPD_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc5 $data
}

proc mc_0xc5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc5]

    return $rdata
}

proc mc_LPC_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc5 0 16 $data 
} 
 
proc mc_LPC_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc5 0 16 ] 

    return $rdata 
}

proc mc_LPC_SR_CTRLUPD_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc5 16 1 $data 
} 
 
proc mc_LPC_SR_CTRLUPD_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc5 16 1 ] 

    return $rdata 
}

proc mc_LPC_SR_PHYUPD_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc5 24 1 $data 
} 
 
proc mc_LPC_SR_PHYUPD_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc5 24 1 ] 

    return $rdata 
}

#################################

proc mc_0xc6_print {} {
    puts "addr: 0xc6"
    #fields
    puts "field_name   :LPC_SR_PHYMSTR_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :LPC_SR_ZQ_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :10 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc6 $data
}

proc mc_0xc6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc6]

    return $rdata
}

proc mc_LPC_SR_PHYMSTR_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc6 0 1 $data 
} 
 
proc mc_LPC_SR_PHYMSTR_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc6 0 1 ] 

    return $rdata 
}

proc mc_LPC_SR_ZQ_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc6 8 1 $data 
} 
 
proc mc_LPC_SR_ZQ_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc6 8 1 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc6 16 10 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc6 16 10 ] 

    return $rdata 
}

#################################

proc mc_0xc7_print {} {
    puts "addr: 0xc7"
    #fields
    puts "field_name   :DFS_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :CURRENT_REG_COPY "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :INIT_FREQ "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0xc7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc7 $data
}

proc mc_0xc7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc7]

    return $rdata
}

proc mc_DFS_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc7 0 1 $data 
} 
 
proc mc_DFS_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc7 0 1 ] 

    return $rdata 
}

proc mc_CURRENT_REG_COPY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc7 8 1 $data 
} 
 
proc mc_CURRENT_REG_COPY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc7 8 1 ] 

    return $rdata 
}

proc mc_INIT_FREQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc7 16 1 $data 
} 
 
proc mc_INIT_FREQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc7 16 1 ] 

    return $rdata 
}

#################################

proc mc_0xc8_print {} {
    puts "addr: 0xc8"
    #fields
    puts "field_name   :TDFI_INIT_START_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0xc02 "
} 

proc mc_0xc8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc8 $data
}

proc mc_0xc8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc8]

    return $rdata
}

proc mc_TDFI_INIT_START_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc8 0 24 $data 
} 
 
proc mc_TDFI_INIT_START_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc8 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xc9_print {} {
    puts "addr: 0xc9"
    #fields
    puts "field_name   :TDFI_INIT_COMPLETE_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x1e8482 "
} 

proc mc_0xc9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xc9 $data
}

proc mc_0xc9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xc9]

    return $rdata
}

proc mc_TDFI_INIT_COMPLETE_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xc9 0 24 $data 
} 
 
proc mc_TDFI_INIT_COMPLETE_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xc9 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xca_print {} {
    puts "addr: 0xca"
    #fields
    puts "field_name   :TDFI_INIT_START_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0xc02 "
} 

proc mc_0xca_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xca $data
}

proc mc_0xca_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xca]

    return $rdata
}

proc mc_TDFI_INIT_START_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xca 0 24 $data 
} 
 
proc mc_TDFI_INIT_START_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xca 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xcb_print {} {
    puts "addr: 0xcb"
    #fields
    puts "field_name   :TDFI_INIT_COMPLETE_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x1e8482 "
} 

proc mc_0xcb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xcb $data
}

proc mc_0xcb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xcb]

    return $rdata
}

proc mc_TDFI_INIT_COMPLETE_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xcb 0 24 $data 
} 
 
proc mc_TDFI_INIT_COMPLETE_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xcb 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xcc_print {} {
    puts "addr: 0xcc"
    #fields
    puts "field_name   :WRITE_MODEREG "
    puts "field_access :RW+ "
    puts "field_bitpos :0 "
    puts "field_size   :27 "
    puts "default field_value  :0x0 "
} 

proc mc_0xcc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xcc $data
}

proc mc_0xcc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xcc]

    return $rdata
}

proc mc_WRITE_MODEREG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xcc 0 27 $data 
} 
 
proc mc_WRITE_MODEREG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xcc 0 27 ] 

    return $rdata 
}

#################################

proc mc_0xcd_print {} {
    puts "addr: 0xcd"
    #fields
    puts "field_name   :MRW_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :READ_MODEREG "
    puts "field_access :RW+ "
    puts "field_bitpos :8 "
    puts "field_size   :17 "
    puts "default field_value  :0x0 "
} 

proc mc_0xcd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xcd $data
}

proc mc_0xcd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xcd]

    return $rdata
}

proc mc_MRW_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xcd 0 8 $data 
} 
 
proc mc_MRW_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xcd 0 8 ] 

    return $rdata 
}

proc mc_READ_MODEREG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xcd 8 17 $data 
} 
 
proc mc_READ_MODEREG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xcd 8 17 ] 

    return $rdata 
}

#################################

proc mc_0xce_print {} {
    puts "addr: 0xce"
    #fields
    puts "field_name   :PERIPHERAL_MRR_DATA_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xce_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xce $data
}

proc mc_0xce_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xce]

    return $rdata
}

proc mc_PERIPHERAL_MRR_DATA_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xce 0 32 $data 
} 
 
proc mc_PERIPHERAL_MRR_DATA_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xce 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xcf_print {} {
    puts "addr: 0xcf"
    #fields
    puts "field_name   :PERIPHERAL_MRR_DATA_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xcf_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xcf $data
}

proc mc_0xcf_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xcf]

    return $rdata
}

proc mc_PERIPHERAL_MRR_DATA_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xcf 0 32 $data 
} 
 
proc mc_PERIPHERAL_MRR_DATA_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xcf 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xd0_print {} {
    puts "addr: 0xd0"
    #fields
    puts "field_name   :PERIPHERAL_MRR_DATA_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd0 $data
}

proc mc_0xd0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd0]

    return $rdata
}

proc mc_PERIPHERAL_MRR_DATA_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd0 0 32 $data 
} 
 
proc mc_PERIPHERAL_MRR_DATA_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd0 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xd1_print {} {
    puts "addr: 0xd1"
    #fields
    puts "field_name   :PERIPHERAL_MRR_DATA_PART_3 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd1 $data
}

proc mc_0xd1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd1]

    return $rdata
}

proc mc_PERIPHERAL_MRR_DATA_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd1 0 32 $data 
} 
 
proc mc_PERIPHERAL_MRR_DATA_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd1 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xd2_print {} {
    puts "addr: 0xd2"
    #fields
    puts "field_name   :PERIPHERAL_MRR_DATA_PART_4 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :24 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd2 $data
}

proc mc_0xd2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd2]

    return $rdata
}

proc mc_PERIPHERAL_MRR_DATA_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd2 0 24 $data 
} 
 
proc mc_PERIPHERAL_MRR_DATA_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd2 0 24 ] 

    return $rdata 
}

#################################

proc mc_0xd6_print {} {
    puts "addr: 0xd6"
    #fields
    puts "field_name   :MRR_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd6 $data
}

proc mc_0xd6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd6]

    return $rdata
}

proc mc_MRR_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd6 8 16 $data 
} 
 
proc mc_MRR_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd6 8 16 ] 

    return $rdata 
}

#################################

proc mc_0xd7_print {} {
    puts "addr: 0xd7"
    #fields
    puts "field_name   :MRR_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :MRW_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd7 $data
}

proc mc_0xd7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd7]

    return $rdata
}

proc mc_MRR_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd7 0 16 $data 
} 
 
proc mc_MRR_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd7 0 16 ] 

    return $rdata 
}

proc mc_MRW_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd7 16 16 $data 
} 
 
proc mc_MRW_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd7 16 16 ] 

    return $rdata 
}

#################################

proc mc_0xd8_print {} {
    puts "addr: 0xd8"
    #fields
    puts "field_name   :MRW_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :MR4_DLL_RST "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :READ_MPR "
    puts "field_access :RW+ "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd8 $data
}

proc mc_0xd8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd8]

    return $rdata
}

proc mc_MRW_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd8 0 16 $data 
} 
 
proc mc_MRW_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd8 0 16 ] 

    return $rdata 
}

proc mc_MR4_DLL_RST_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd8 16 1 $data 
} 
 
proc mc_MR4_DLL_RST_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd8 16 1 ] 

    return $rdata 
}

proc mc_READ_MPR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd8 24 4 $data 
} 
 
proc mc_READ_MPR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd8 24 4 ] 

    return $rdata 
}

#################################

proc mc_0xd9_print {} {
    puts "addr: 0xd9"
    #fields
    puts "field_name   :MPRR_DATA_0_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xd9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xd9 $data
}

proc mc_0xd9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xd9]

    return $rdata
}

proc mc_MPRR_DATA_0_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xd9 0 32 $data 
} 
 
proc mc_MPRR_DATA_0_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xd9 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xda_print {} {
    puts "addr: 0xda"
    #fields
    puts "field_name   :MPRR_DATA_0_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xda_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xda $data
}

proc mc_0xda_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xda]

    return $rdata
}

proc mc_MPRR_DATA_0_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xda 0 32 $data 
} 
 
proc mc_MPRR_DATA_0_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xda 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xdb_print {} {
    puts "addr: 0xdb"
    #fields
    puts "field_name   :MPRR_DATA_0_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0xdb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xdb $data
}

proc mc_0xdb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xdb]

    return $rdata
}

proc mc_MPRR_DATA_0_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xdb 0 8 $data 
} 
 
proc mc_MPRR_DATA_0_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xdb 0 8 ] 

    return $rdata 
}

#################################

proc mc_0xdc_print {} {
    puts "addr: 0xdc"
    #fields
    puts "field_name   :MPRR_DATA_1_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xdc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xdc $data
}

proc mc_0xdc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xdc]

    return $rdata
}

proc mc_MPRR_DATA_1_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xdc 0 32 $data 
} 
 
proc mc_MPRR_DATA_1_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xdc 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xdd_print {} {
    puts "addr: 0xdd"
    #fields
    puts "field_name   :MPRR_DATA_1_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xdd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xdd $data
}

proc mc_0xdd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xdd]

    return $rdata
}

proc mc_MPRR_DATA_1_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xdd 0 32 $data 
} 
 
proc mc_MPRR_DATA_1_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xdd 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xde_print {} {
    puts "addr: 0xde"
    #fields
    puts "field_name   :MPRR_DATA_1_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0xde_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xde $data
}

proc mc_0xde_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xde]

    return $rdata
}

proc mc_MPRR_DATA_1_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xde 0 8 $data 
} 
 
proc mc_MPRR_DATA_1_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xde 0 8 ] 

    return $rdata 
}

#################################

proc mc_0xdf_print {} {
    puts "addr: 0xdf"
    #fields
    puts "field_name   :MPRR_DATA_2_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xdf_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xdf $data
}

proc mc_0xdf_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xdf]

    return $rdata
}

proc mc_MPRR_DATA_2_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xdf 0 32 $data 
} 
 
proc mc_MPRR_DATA_2_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xdf 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xe0_print {} {
    puts "addr: 0xe0"
    #fields
    puts "field_name   :MPRR_DATA_2_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe0 $data
}

proc mc_0xe0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe0]

    return $rdata
}

proc mc_MPRR_DATA_2_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe0 0 32 $data 
} 
 
proc mc_MPRR_DATA_2_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe0 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xe1_print {} {
    puts "addr: 0xe1"
    #fields
    puts "field_name   :MPRR_DATA_2_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe1 $data
}

proc mc_0xe1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe1]

    return $rdata
}

proc mc_MPRR_DATA_2_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe1 0 8 $data 
} 
 
proc mc_MPRR_DATA_2_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe1 0 8 ] 

    return $rdata 
}

#################################

proc mc_0xe2_print {} {
    puts "addr: 0xe2"
    #fields
    puts "field_name   :MPRR_DATA_3_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe2 $data
}

proc mc_0xe2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe2]

    return $rdata
}

proc mc_MPRR_DATA_3_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe2 0 32 $data 
} 
 
proc mc_MPRR_DATA_3_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe2 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xe3_print {} {
    puts "addr: 0xe3"
    #fields
    puts "field_name   :MPRR_DATA_3_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe3 $data
}

proc mc_0xe3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe3]

    return $rdata
}

proc mc_MPRR_DATA_3_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe3 0 32 $data 
} 
 
proc mc_MPRR_DATA_3_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe3 0 32 ] 

    return $rdata 
}

#################################

proc mc_0xe4_print {} {
    puts "addr: 0xe4"
    #fields
    puts "field_name   :MPRR_DATA_3_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :MR0_DATA_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :18 "
    puts "default field_value  :0x30 "
} 

proc mc_0xe4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe4 $data
}

proc mc_0xe4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe4]

    return $rdata
}

proc mc_MPRR_DATA_3_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe4 0 8 $data 
} 
 
proc mc_MPRR_DATA_3_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe4 0 8 ] 

    return $rdata 
}

proc mc_MR0_DATA_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe4 8 18 $data 
} 
 
proc mc_MR0_DATA_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe4 8 18 ] 

    return $rdata 
}

#################################

proc mc_0xe5_print {} {
    puts "addr: 0xe5"
    #fields
    puts "field_name   :MR1_DATA_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe5 $data
}

proc mc_0xe5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe5]

    return $rdata
}

proc mc_MR1_DATA_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe5 0 18 $data 
} 
 
proc mc_MR1_DATA_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe5 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xe6_print {} {
    puts "addr: 0xe6"
    #fields
    puts "field_name   :MR2_DATA_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe6 $data
}

proc mc_0xe6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe6]

    return $rdata
}

proc mc_MR2_DATA_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe6 0 18 $data 
} 
 
proc mc_MR2_DATA_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe6 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xe7_print {} {
    puts "addr: 0xe7"
    #fields
    puts "field_name   :MR0_DATA_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x30 "
} 

proc mc_0xe7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe7 $data
}

proc mc_0xe7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe7]

    return $rdata
}

proc mc_MR0_DATA_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe7 0 18 $data 
} 
 
proc mc_MR0_DATA_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe7 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xe8_print {} {
    puts "addr: 0xe8"
    #fields
    puts "field_name   :MR1_DATA_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe8 $data
}

proc mc_0xe8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe8]

    return $rdata
}

proc mc_MR1_DATA_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe8 0 18 $data 
} 
 
proc mc_MR1_DATA_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe8 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xe9_print {} {
    puts "addr: 0xe9"
    #fields
    puts "field_name   :MR2_DATA_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xe9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xe9 $data
}

proc mc_0xe9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xe9]

    return $rdata
}

proc mc_MR2_DATA_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xe9 0 18 $data 
} 
 
proc mc_MR2_DATA_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xe9 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xea_print {} {
    puts "addr: 0xea"
    #fields
    puts "field_name   :MR0_DATA_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x30 "
} 

proc mc_0xea_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xea $data
}

proc mc_0xea_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xea]

    return $rdata
}

proc mc_MR0_DATA_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xea 0 18 $data 
} 
 
proc mc_MR0_DATA_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xea 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xeb_print {} {
    puts "addr: 0xeb"
    #fields
    puts "field_name   :MR1_DATA_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xeb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xeb $data
}

proc mc_0xeb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xeb]

    return $rdata
}

proc mc_MR1_DATA_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xeb 0 18 $data 
} 
 
proc mc_MR1_DATA_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xeb 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xec_print {} {
    puts "addr: 0xec"
    #fields
    puts "field_name   :MR2_DATA_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xec_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xec $data
}

proc mc_0xec_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xec]

    return $rdata
}

proc mc_MR2_DATA_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xec 0 18 $data 
} 
 
proc mc_MR2_DATA_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xec 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xed_print {} {
    puts "addr: 0xed"
    #fields
    puts "field_name   :MR0_DATA_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x30 "
} 

proc mc_0xed_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xed $data
}

proc mc_0xed_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xed]

    return $rdata
}

proc mc_MR0_DATA_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xed 0 18 $data 
} 
 
proc mc_MR0_DATA_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xed 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xee_print {} {
    puts "addr: 0xee"
    #fields
    puts "field_name   :MR1_DATA_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xee_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xee $data
}

proc mc_0xee_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xee]

    return $rdata
}

proc mc_MR1_DATA_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xee 0 18 $data 
} 
 
proc mc_MR1_DATA_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xee 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xef_print {} {
    puts "addr: 0xef"
    #fields
    puts "field_name   :MR2_DATA_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xef_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xef $data
}

proc mc_0xef_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xef]

    return $rdata
}

proc mc_MR2_DATA_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xef 0 18 $data 
} 
 
proc mc_MR2_DATA_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xef 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf0_print {} {
    puts "addr: 0xf0"
    #fields
    puts "field_name   :MRSINGLE_DATA_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf0 $data
}

proc mc_0xf0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf0]

    return $rdata
}

proc mc_MRSINGLE_DATA_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf0 0 18 $data 
} 
 
proc mc_MRSINGLE_DATA_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf0 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf1_print {} {
    puts "addr: 0xf1"
    #fields
    puts "field_name   :MRSINGLE_DATA_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf1 $data
}

proc mc_0xf1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf1]

    return $rdata
}

proc mc_MRSINGLE_DATA_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf1 0 18 $data 
} 
 
proc mc_MRSINGLE_DATA_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf1 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf2_print {} {
    puts "addr: 0xf2"
    #fields
    puts "field_name   :MR3_DATA_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf2 $data
}

proc mc_0xf2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf2]

    return $rdata
}

proc mc_MR3_DATA_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf2 0 18 $data 
} 
 
proc mc_MR3_DATA_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf2 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf3_print {} {
    puts "addr: 0xf3"
    #fields
    puts "field_name   :MR3_DATA_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf3 $data
}

proc mc_0xf3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf3]

    return $rdata
}

proc mc_MR3_DATA_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf3 0 18 $data 
} 
 
proc mc_MR3_DATA_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf3 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf4_print {} {
    puts "addr: 0xf4"
    #fields
    puts "field_name   :MR3_DATA_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf4 $data
}

proc mc_0xf4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf4]

    return $rdata
}

proc mc_MR3_DATA_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf4 0 18 $data 
} 
 
proc mc_MR3_DATA_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf4 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf5_print {} {
    puts "addr: 0xf5"
    #fields
    puts "field_name   :MR3_DATA_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf5 $data
}

proc mc_0xf5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf5]

    return $rdata
}

proc mc_MR3_DATA_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf5 0 18 $data 
} 
 
proc mc_MR3_DATA_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf5 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf6_print {} {
    puts "addr: 0xf6"
    #fields
    puts "field_name   :MR4_DATA_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf6 $data
}

proc mc_0xf6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf6]

    return $rdata
}

proc mc_MR4_DATA_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf6 0 18 $data 
} 
 
proc mc_MR4_DATA_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf6 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf7_print {} {
    puts "addr: 0xf7"
    #fields
    puts "field_name   :MR4_DATA_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf7 $data
}

proc mc_0xf7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf7]

    return $rdata
}

proc mc_MR4_DATA_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf7 0 18 $data 
} 
 
proc mc_MR4_DATA_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf7 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf8_print {} {
    puts "addr: 0xf8"
    #fields
    puts "field_name   :MR4_DATA_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf8 $data
}

proc mc_0xf8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf8]

    return $rdata
}

proc mc_MR4_DATA_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf8 0 18 $data 
} 
 
proc mc_MR4_DATA_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf8 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xf9_print {} {
    puts "addr: 0xf9"
    #fields
    puts "field_name   :MR4_DATA_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x0 "
} 

proc mc_0xf9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xf9 $data
}

proc mc_0xf9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xf9]

    return $rdata
}

proc mc_MR4_DATA_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xf9 0 18 $data 
} 
 
proc mc_MR4_DATA_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xf9 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xfa_print {} {
    puts "addr: 0xfa"
    #fields
    puts "field_name   :MR5_DATA_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x62 "
} 

proc mc_0xfa_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xfa $data
}

proc mc_0xfa_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xfa]

    return $rdata
}

proc mc_MR5_DATA_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xfa 0 18 $data 
} 
 
proc mc_MR5_DATA_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xfa 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xfb_print {} {
    puts "addr: 0xfb"
    #fields
    puts "field_name   :MR5_DATA_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x62 "
} 

proc mc_0xfb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xfb $data
}

proc mc_0xfb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xfb]

    return $rdata
}

proc mc_MR5_DATA_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xfb 0 18 $data 
} 
 
proc mc_MR5_DATA_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xfb 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xfc_print {} {
    puts "addr: 0xfc"
    #fields
    puts "field_name   :MR5_DATA_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x62 "
} 

proc mc_0xfc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xfc $data
}

proc mc_0xfc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xfc]

    return $rdata
}

proc mc_MR5_DATA_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xfc 0 18 $data 
} 
 
proc mc_MR5_DATA_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xfc 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xfd_print {} {
    puts "addr: 0xfd"
    #fields
    puts "field_name   :MR5_DATA_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x62 "
} 

proc mc_0xfd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xfd $data
}

proc mc_0xfd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xfd]

    return $rdata
}

proc mc_MR5_DATA_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xfd 0 18 $data 
} 
 
proc mc_MR5_DATA_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xfd 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xfe_print {} {
    puts "addr: 0xfe"
    #fields
    puts "field_name   :MR6_DATA_F0_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x2800 "
} 

proc mc_0xfe_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xfe $data
}

proc mc_0xfe_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xfe]

    return $rdata
}

proc mc_MR6_DATA_F0_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xfe 0 18 $data 
} 
 
proc mc_MR6_DATA_F0_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xfe 0 18 ] 

    return $rdata 
}

#################################

proc mc_0xff_print {} {
    puts "addr: 0xff"
    #fields
    puts "field_name   :MR6_DATA_F1_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x2800 "
} 

proc mc_0xff_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0xff $data
}

proc mc_0xff_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0xff]

    return $rdata
}

proc mc_MR6_DATA_F1_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0xff 0 18 $data 
} 
 
proc mc_MR6_DATA_F1_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0xff 0 18 ] 

    return $rdata 
}

#################################

proc mc_0x100_print {} {
    puts "addr: 0x100"
    #fields
    puts "field_name   :MR6_DATA_F0_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x2800 "
} 

proc mc_0x100_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x100 $data
}

proc mc_0x100_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x100]

    return $rdata
}

proc mc_MR6_DATA_F0_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x100 0 18 $data 
} 
 
proc mc_MR6_DATA_F0_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x100 0 18 ] 

    return $rdata 
}

#################################

proc mc_0x101_print {} {
    puts "addr: 0x101"
    #fields
    puts "field_name   :MR6_DATA_F1_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :18 "
    puts "default field_value  :0x2800 "
} 

proc mc_0x101_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x101 $data
}

proc mc_0x101_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x101]

    return $rdata
}

proc mc_MR6_DATA_F1_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x101 0 18 $data 
} 
 
proc mc_MR6_DATA_F1_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x101 0 18 ] 

    return $rdata 
}

#################################

proc mc_0x102_print {} {
    puts "addr: 0x102"
    #fields
    puts "field_name   :MPRR_SW_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :MPRR_SW_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x102_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x102 $data
}

proc mc_0x102_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x102]

    return $rdata
}

proc mc_MPRR_SW_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x102 0 16 $data 
} 
 
proc mc_MPRR_SW_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x102 0 16 ] 

    return $rdata 
}

proc mc_MPRR_SW_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x102 16 16 $data 
} 
 
proc mc_MPRR_SW_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x102 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x103_print {} {
    puts "addr: 0x103"
    #fields
    puts "field_name   :BIST_GO "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ADDR_SPACE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :6 "
    puts "default field_value  :0x0 "
    puts "field_name   :BIST_DATA_CHECK "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x103_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x103 $data
}

proc mc_0x103_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x103]

    return $rdata
}

proc mc_BIST_GO_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x103 0 1 $data 
} 
 
proc mc_BIST_GO_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x103 0 1 ] 

    return $rdata 
}

proc mc_ADDR_SPACE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x103 16 6 $data 
} 
 
proc mc_ADDR_SPACE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x103 16 6 ] 

    return $rdata 
}

proc mc_BIST_DATA_CHECK_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x103 24 1 $data 
} 
 
proc mc_BIST_DATA_CHECK_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x103 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x104_print {} {
    puts "addr: 0x104"
    #fields
    puts "field_name   :BIST_ECC_LANE_CHECK "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x104_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x104 $data
}

proc mc_0x104_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x104]

    return $rdata
}

proc mc_BIST_ECC_LANE_CHECK_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x104 0 1 $data 
} 
 
proc mc_BIST_ECC_LANE_CHECK_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x104 0 1 ] 

    return $rdata 
}

#################################

proc mc_0x105_print {} {
    puts "addr: 0x105"
    #fields
    puts "field_name   :BIST_START_ADDRESS_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x105_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x105 $data
}

proc mc_0x105_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x105]

    return $rdata
}

proc mc_BIST_START_ADDRESS_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x105 0 32 $data 
} 
 
proc mc_BIST_START_ADDRESS_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x105 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x106_print {} {
    puts "addr: 0x106"
    #fields
    puts "field_name   :BIST_START_ADDRESS_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0x106_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x106 $data
}

proc mc_0x106_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x106]

    return $rdata
}

proc mc_BIST_START_ADDRESS_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x106 0 7 $data 
} 
 
proc mc_BIST_START_ADDRESS_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x106 0 7 ] 

    return $rdata 
}

#################################

proc mc_0x10b_print {} {
    puts "addr: 0x10b"
    #fields
    puts "field_name   :BIST_TEST_MODE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
} 

proc mc_0x10b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x10b $data
}

proc mc_0x10b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x10b]

    return $rdata
}

proc mc_BIST_TEST_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x10b 16 3 $data 
} 
 
proc mc_BIST_TEST_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x10b 16 3 ] 

    return $rdata 
}

#################################

proc mc_0x115_print {} {
    puts "addr: 0x115"
    #fields
    puts "field_name   :BIST_RET_STATE "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :BIST_ERR_STOP "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :12 "
    puts "default field_value  :0x0 "
} 

proc mc_0x115_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x115 $data
}

proc mc_0x115_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x115]

    return $rdata
}

proc mc_BIST_RET_STATE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x115 0 1 $data 
} 
 
proc mc_BIST_RET_STATE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x115 0 1 ] 

    return $rdata 
}

proc mc_BIST_ERR_STOP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x115 8 12 $data 
} 
 
proc mc_BIST_ERR_STOP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x115 8 12 ] 

    return $rdata 
}

#################################

proc mc_0x116_print {} {
    puts "addr: 0x116"
    #fields
    puts "field_name   :BIST_ERR_COUNT "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0x0 "
    puts "field_name   :BIST_RET_STATE_EXIT "
    puts "field_access :WR "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x116_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x116 $data
}

proc mc_0x116_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x116]

    return $rdata
}

proc mc_BIST_ERR_COUNT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x116 0 12 $data 
} 
 
proc mc_BIST_ERR_COUNT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x116 0 12 ] 

    return $rdata 
}

proc mc_BIST_RET_STATE_EXIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x116 16 1 $data 
} 
 
proc mc_BIST_RET_STATE_EXIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x116 16 1 ] 

    return $rdata 
}

proc mc_ECC_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x116 24 2 $data 
} 
 
proc mc_ECC_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x116 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x117_print {} {
    puts "addr: 0x117"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW+ "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x117_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x117 $data
}

proc mc_0x117_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x117]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x117 0 1 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x117 0 1 ] 

    return $rdata 
}

#################################

proc mc_0x119_print {} {
    puts "addr: 0x119"
    #fields
    puts "field_name   :ECC_DISABLE_W_UC_ERR "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_WRITEBACK_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x119_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x119 $data
}

proc mc_0x119_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x119]

    return $rdata
}

proc mc_ECC_DISABLE_W_UC_ERR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x119 0 1 $data 
} 
 
proc mc_ECC_DISABLE_W_UC_ERR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x119 0 1 ] 

    return $rdata 
}

proc mc_ECC_WRITEBACK_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x119 8 1 $data 
} 
 
proc mc_ECC_WRITEBACK_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x119 8 1 ] 

    return $rdata 
}

#################################

proc mc_0x11a_print {} {
    puts "addr: 0x11a"
    #fields
    puts "field_name   :ECC_U_ADDR_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x11a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x11a $data
}

proc mc_0x11a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x11a]

    return $rdata
}

proc mc_ECC_U_ADDR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11a 0 32 $data 
} 
 
proc mc_ECC_U_ADDR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x11b_print {} {
    puts "addr: 0x11b"
    #fields
    puts "field_name   :ECC_U_ADDR_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_U_SYND "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x11b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x11b $data
}

proc mc_0x11b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x11b]

    return $rdata
}

proc mc_ECC_U_ADDR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11b 0 7 $data 
} 
 
proc mc_ECC_U_ADDR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11b 0 7 ] 

    return $rdata 
}

proc mc_ECC_U_SYND_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11b 8 8 $data 
} 
 
proc mc_ECC_U_SYND_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11b 8 8 ] 

    return $rdata 
}

#################################

proc mc_0x11c_print {} {
    puts "addr: 0x11c"
    #fields
    puts "field_name   :ECC_U_DATA_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x11c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x11c $data
}

proc mc_0x11c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x11c]

    return $rdata
}

proc mc_ECC_U_DATA_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11c 0 32 $data 
} 
 
proc mc_ECC_U_DATA_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x11d_print {} {
    puts "addr: 0x11d"
    #fields
    puts "field_name   :ECC_U_DATA_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x11d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x11d $data
}

proc mc_0x11d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x11d]

    return $rdata
}

proc mc_ECC_U_DATA_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11d 0 32 $data 
} 
 
proc mc_ECC_U_DATA_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x11e_print {} {
    puts "addr: 0x11e"
    #fields
    puts "field_name   :ECC_C_ADDR_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x11e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x11e $data
}

proc mc_0x11e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x11e]

    return $rdata
}

proc mc_ECC_C_ADDR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11e 0 32 $data 
} 
 
proc mc_ECC_C_ADDR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x11f_print {} {
    puts "addr: 0x11f"
    #fields
    puts "field_name   :ECC_C_ADDR_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_C_SYND "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x11f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x11f $data
}

proc mc_0x11f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x11f]

    return $rdata
}

proc mc_ECC_C_ADDR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11f 0 7 $data 
} 
 
proc mc_ECC_C_ADDR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11f 0 7 ] 

    return $rdata 
}

proc mc_ECC_C_SYND_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x11f 8 8 $data 
} 
 
proc mc_ECC_C_SYND_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x11f 8 8 ] 

    return $rdata 
}

#################################

proc mc_0x120_print {} {
    puts "addr: 0x120"
    #fields
    puts "field_name   :ECC_C_DATA_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x120_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x120 $data
}

proc mc_0x120_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x120]

    return $rdata
}

proc mc_ECC_C_DATA_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x120 0 32 $data 
} 
 
proc mc_ECC_C_DATA_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x120 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x121_print {} {
    puts "addr: 0x121"
    #fields
    puts "field_name   :ECC_C_DATA_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x121_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x121 $data
}

proc mc_0x121_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x121]

    return $rdata
}

proc mc_ECC_C_DATA_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x121 0 32 $data 
} 
 
proc mc_ECC_C_DATA_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x121 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x122_print {} {
    puts "addr: 0x122"
    #fields
    puts "field_name   :ECC_U_ID "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :15 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_C_ID "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :15 "
    puts "default field_value  :0x0 "
} 

proc mc_0x122_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x122 $data
}

proc mc_0x122_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x122]

    return $rdata
}

proc mc_ECC_U_ID_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x122 0 15 $data 
} 
 
proc mc_ECC_U_ID_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x122 0 15 ] 

    return $rdata 
}

proc mc_ECC_C_ID_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x122 16 15 $data 
} 
 
proc mc_ECC_C_ID_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x122 16 15 ] 

    return $rdata 
}

#################################

proc mc_0x12c_print {} {
    puts "addr: 0x12c"
    #fields
    puts "field_name   :ECC_SCRUB_START "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_SCRUB_IN_PROGRESS "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_SCRUB_LEN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :13 "
    puts "default field_value  :0x20 "
} 

proc mc_0x12c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x12c $data
}

proc mc_0x12c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x12c]

    return $rdata
}

proc mc_ECC_SCRUB_START_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12c 0 1 $data 
} 
 
proc mc_ECC_SCRUB_START_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12c 0 1 ] 

    return $rdata 
}

proc mc_ECC_SCRUB_IN_PROGRESS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12c 8 1 $data 
} 
 
proc mc_ECC_SCRUB_IN_PROGRESS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12c 8 1 ] 

    return $rdata 
}

proc mc_ECC_SCRUB_LEN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12c 16 13 $data 
} 
 
proc mc_ECC_SCRUB_LEN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12c 16 13 ] 

    return $rdata 
}

#################################

proc mc_0x12d_print {} {
    puts "addr: 0x12d"
    #fields
    puts "field_name   :ECC_SCRUB_MODE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ECC_SCRUB_INTERVAL "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x3e8 "
} 

proc mc_0x12d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x12d $data
}

proc mc_0x12d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x12d]

    return $rdata
}

proc mc_ECC_SCRUB_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12d 0 1 $data 
} 
 
proc mc_ECC_SCRUB_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12d 0 1 ] 

    return $rdata 
}

proc mc_ECC_SCRUB_INTERVAL_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12d 8 16 $data 
} 
 
proc mc_ECC_SCRUB_INTERVAL_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12d 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x12e_print {} {
    puts "addr: 0x12e"
    #fields
    puts "field_name   :ECC_SCRUB_IDLE_CNT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x64 "
} 

proc mc_0x12e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x12e $data
}

proc mc_0x12e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x12e]

    return $rdata
}

proc mc_ECC_SCRUB_IDLE_CNT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12e 0 16 $data 
} 
 
proc mc_ECC_SCRUB_IDLE_CNT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12e 0 16 ] 

    return $rdata 
}

#################################

proc mc_0x12f_print {} {
    puts "addr: 0x12f"
    #fields
    puts "field_name   :ECC_SCRUB_START_ADDR_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x12f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x12f $data
}

proc mc_0x12f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x12f]

    return $rdata
}

proc mc_ECC_SCRUB_START_ADDR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x12f 0 32 $data 
} 
 
proc mc_ECC_SCRUB_START_ADDR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x12f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x130_print {} {
    puts "addr: 0x130"
    #fields
    puts "field_name   :ECC_SCRUB_START_ADDR_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0x130_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x130 $data
}

proc mc_0x130_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x130]

    return $rdata
}

proc mc_ECC_SCRUB_START_ADDR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x130 0 7 $data 
} 
 
proc mc_ECC_SCRUB_START_ADDR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x130 0 7 ] 

    return $rdata 
}

#################################

proc mc_0x131_print {} {
    puts "addr: 0x131"
    #fields
    puts "field_name   :ECC_SCRUB_END_ADDR_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x131_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x131 $data
}

proc mc_0x131_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x131]

    return $rdata
}

proc mc_ECC_SCRUB_END_ADDR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x131 0 32 $data 
} 
 
proc mc_ECC_SCRUB_END_ADDR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x131 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x132_print {} {
    puts "addr: 0x132"
    #fields
    puts "field_name   :ECC_SCRUB_END_ADDR_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :CRC_MODE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
} 

proc mc_0x132_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x132 $data
}

proc mc_0x132_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x132]

    return $rdata
}

proc mc_ECC_SCRUB_END_ADDR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x132 0 7 $data 
} 
 
proc mc_ECC_SCRUB_END_ADDR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x132 0 7 ] 

    return $rdata 
}

proc mc_CRC_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x132 8 3 $data 
} 
 
proc mc_CRC_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x132 8 3 ] 

    return $rdata 
}

#################################

proc mc_0x133_print {} {
    puts "addr: 0x133"
    #fields
    puts "field_name   :DQ_MAP_0_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x133_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x133 $data
}

proc mc_0x133_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x133]

    return $rdata
}

proc mc_DQ_MAP_0_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x133 0 32 $data 
} 
 
proc mc_DQ_MAP_0_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x133 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x134_print {} {
    puts "addr: 0x134"
    #fields
    puts "field_name   :DQ_MAP_0_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x134_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x134 $data
}

proc mc_0x134_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x134]

    return $rdata
}

proc mc_DQ_MAP_0_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x134 0 32 $data 
} 
 
proc mc_DQ_MAP_0_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x134 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x135_print {} {
    puts "addr: 0x135"
    #fields
    puts "field_name   :DQ_MAP_0_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x135_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x135 $data
}

proc mc_0x135_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x135]

    return $rdata
}

proc mc_DQ_MAP_0_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x135 0 32 $data 
} 
 
proc mc_DQ_MAP_0_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x135 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x136_print {} {
    puts "addr: 0x136"
    #fields
    puts "field_name   :DQ_MAP_0_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x136_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x136 $data
}

proc mc_0x136_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x136]

    return $rdata
}

proc mc_DQ_MAP_0_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x136 0 32 $data 
} 
 
proc mc_DQ_MAP_0_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x136 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x137_print {} {
    puts "addr: 0x137"
    #fields
    puts "field_name   :DQ_MAP_0_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQ_MAP_ODD_RANK_SWAP_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x137_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x137 $data
}

proc mc_0x137_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x137]

    return $rdata
}

proc mc_DQ_MAP_0_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x137 0 16 $data 
} 
 
proc mc_DQ_MAP_0_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x137 0 16 ] 

    return $rdata 
}

proc mc_DQ_MAP_ODD_RANK_SWAP_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x137 16 2 $data 
} 
 
proc mc_DQ_MAP_ODD_RANK_SWAP_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x137 16 2 ] 

    return $rdata 
}

#################################

proc mc_0x138_print {} {
    puts "addr: 0x138"
    #fields
    puts "field_name   :DQ_MAP_1_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x138_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x138 $data
}

proc mc_0x138_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x138]

    return $rdata
}

proc mc_DQ_MAP_1_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x138 0 32 $data 
} 
 
proc mc_DQ_MAP_1_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x138 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x139_print {} {
    puts "addr: 0x139"
    #fields
    puts "field_name   :DQ_MAP_1_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x139_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x139 $data
}

proc mc_0x139_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x139]

    return $rdata
}

proc mc_DQ_MAP_1_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x139 0 32 $data 
} 
 
proc mc_DQ_MAP_1_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x139 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x13a_print {} {
    puts "addr: 0x13a"
    #fields
    puts "field_name   :DQ_MAP_1_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x13a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x13a $data
}

proc mc_0x13a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x13a]

    return $rdata
}

proc mc_DQ_MAP_1_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13a 0 32 $data 
} 
 
proc mc_DQ_MAP_1_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x13b_print {} {
    puts "addr: 0x13b"
    #fields
    puts "field_name   :DQ_MAP_1_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x13b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x13b $data
}

proc mc_0x13b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x13b]

    return $rdata
}

proc mc_DQ_MAP_1_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13b 0 32 $data 
} 
 
proc mc_DQ_MAP_1_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x13c_print {} {
    puts "addr: 0x13c"
    #fields
    puts "field_name   :DQ_MAP_1_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DQ_MAP_ODD_RANK_SWAP_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :TDFI_PHY_CRC_MAX_LAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x53 "
} 

proc mc_0x13c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x13c $data
}

proc mc_0x13c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x13c]

    return $rdata
}

proc mc_DQ_MAP_1_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13c 0 16 $data 
} 
 
proc mc_DQ_MAP_1_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13c 0 16 ] 

    return $rdata 
}

proc mc_DQ_MAP_ODD_RANK_SWAP_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13c 16 2 $data 
} 
 
proc mc_DQ_MAP_ODD_RANK_SWAP_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13c 16 2 ] 

    return $rdata 
}

proc mc_TDFI_PHY_CRC_MAX_LAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13c 24 8 $data 
} 
 
proc mc_TDFI_PHY_CRC_MAX_LAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13c 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x13d_print {} {
    puts "addr: 0x13d"
    #fields
    puts "field_name   :TDFI_PHY_CRC_MAX_LAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x53 "
    puts "field_name   :CRC_RETRY_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :CRC_ALERT_N_MAX_PW "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x5 "
    puts "field_name   :CRC_RETRY_IN_PROGRESS "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x13d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x13d $data
}

proc mc_0x13d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x13d]

    return $rdata
}

proc mc_TDFI_PHY_CRC_MAX_LAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13d 0 8 $data 
} 
 
proc mc_TDFI_PHY_CRC_MAX_LAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13d 0 8 ] 

    return $rdata 
}

proc mc_CRC_RETRY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13d 8 1 $data 
} 
 
proc mc_CRC_RETRY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13d 8 1 ] 

    return $rdata 
}

proc mc_CRC_ALERT_N_MAX_PW_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13d 16 4 $data 
} 
 
proc mc_CRC_ALERT_N_MAX_PW_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13d 16 4 ] 

    return $rdata 
}

proc mc_CRC_RETRY_IN_PROGRESS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13d 24 1 $data 
} 
 
proc mc_CRC_RETRY_IN_PROGRESS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13d 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x13e_print {} {
    puts "addr: 0x13e"
    #fields
    puts "field_name   :CMD_BLK_SPLIT_SIZE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :LONG_COUNT_MASK "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
    puts "field_name   :AREF_NORM_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x11 "
    puts "field_name   :AREF_HIGH_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x12 "
} 

proc mc_0x13e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x13e $data
}

proc mc_0x13e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x13e]

    return $rdata
}

proc mc_CMD_BLK_SPLIT_SIZE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13e 0 1 $data 
} 
 
proc mc_CMD_BLK_SPLIT_SIZE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13e 0 1 ] 

    return $rdata 
}

proc mc_LONG_COUNT_MASK_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13e 8 5 $data 
} 
 
proc mc_LONG_COUNT_MASK_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13e 8 5 ] 

    return $rdata 
}

proc mc_AREF_NORM_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13e 16 5 $data 
} 
 
proc mc_AREF_NORM_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13e 16 5 ] 

    return $rdata 
}

proc mc_AREF_HIGH_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13e 24 5 $data 
} 
 
proc mc_AREF_HIGH_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13e 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x13f_print {} {
    puts "addr: 0x13f"
    #fields
    puts "field_name   :AREF_MAX_DEFICIT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :5 "
    puts "default field_value  :0x14 "
    puts "field_name   :AREF_MAX_CREDIT "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x10 "
    puts "field_name   :AREF_CMD_MAX_PER_TREFI "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x4 "
    puts "field_name   :AREF_NULL_PEND_EXT_REQ "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x13f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x13f $data
}

proc mc_0x13f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x13f]

    return $rdata
}

proc mc_AREF_MAX_DEFICIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13f 0 5 $data 
} 
 
proc mc_AREF_MAX_DEFICIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13f 0 5 ] 

    return $rdata 
}

proc mc_AREF_MAX_CREDIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13f 8 5 $data 
} 
 
proc mc_AREF_MAX_CREDIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13f 8 5 ] 

    return $rdata 
}

proc mc_AREF_CMD_MAX_PER_TREFI_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13f 16 4 $data 
} 
 
proc mc_AREF_CMD_MAX_PER_TREFI_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13f 16 4 ] 

    return $rdata 
}

proc mc_AREF_NULL_PEND_EXT_REQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x13f 24 1 $data 
} 
 
proc mc_AREF_NULL_PEND_EXT_REQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x13f 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x140_print {} {
    puts "addr: 0x140"
    #fields
    puts "field_name   :ZQCS_OPT_THRESHOLD "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x3 "
    puts "field_name   :ZQ_CALSTART_NORM_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x140_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x140 $data
}

proc mc_0x140_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x140]

    return $rdata
}

proc mc_ZQCS_OPT_THRESHOLD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x140 0 3 $data 
} 
 
proc mc_ZQCS_OPT_THRESHOLD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x140 0 3 ] 

    return $rdata 
}

proc mc_ZQ_CALSTART_NORM_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x140 8 16 $data 
} 
 
proc mc_ZQ_CALSTART_NORM_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x140 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x141_print {} {
    puts "addr: 0x141"
    #fields
    puts "field_name   :ZQ_CALSTART_HIGH_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CALLATCH_HIGH_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x141_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x141 $data
}

proc mc_0x141_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x141]

    return $rdata
}

proc mc_ZQ_CALSTART_HIGH_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x141 0 16 $data 
} 
 
proc mc_ZQ_CALSTART_HIGH_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x141 0 16 ] 

    return $rdata 
}

proc mc_ZQ_CALLATCH_HIGH_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x141 16 16 $data 
} 
 
proc mc_ZQ_CALLATCH_HIGH_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x141 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x142_print {} {
    puts "addr: 0x142"
    #fields
    puts "field_name   :ZQ_CS_NORM_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CS_HIGH_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x142_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x142 $data
}

proc mc_0x142_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x142]

    return $rdata
}

proc mc_ZQ_CS_NORM_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x142 0 16 $data 
} 
 
proc mc_ZQ_CS_NORM_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x142 0 16 ] 

    return $rdata 
}

proc mc_ZQ_CS_HIGH_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x142 16 16 $data 
} 
 
proc mc_ZQ_CS_HIGH_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x142 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x143_print {} {
    puts "addr: 0x143"
    #fields
    puts "field_name   :ZQ_CALSTART_TIMEOUT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CALLATCH_TIMEOUT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x143_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x143 $data
}

proc mc_0x143_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x143]

    return $rdata
}

proc mc_ZQ_CALSTART_TIMEOUT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x143 0 16 $data 
} 
 
proc mc_ZQ_CALSTART_TIMEOUT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x143 0 16 ] 

    return $rdata 
}

proc mc_ZQ_CALLATCH_TIMEOUT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x143 16 16 $data 
} 
 
proc mc_ZQ_CALLATCH_TIMEOUT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x143 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x144_print {} {
    puts "addr: 0x144"
    #fields
    puts "field_name   :ZQ_CS_TIMEOUT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_PROMOTE_THRESHOLD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x144_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x144 $data
}

proc mc_0x144_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x144]

    return $rdata
}

proc mc_ZQ_CS_TIMEOUT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x144 0 16 $data 
} 
 
proc mc_ZQ_CS_TIMEOUT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x144 0 16 ] 

    return $rdata 
}

proc mc_ZQ_PROMOTE_THRESHOLD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x144 16 16 $data 
} 
 
proc mc_ZQ_PROMOTE_THRESHOLD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x144 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x145_print {} {
    puts "addr: 0x145"
    #fields
    puts "field_name   :ZQ_CALSTART_NORM_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CALSTART_HIGH_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x145_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x145 $data
}

proc mc_0x145_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x145]

    return $rdata
}

proc mc_ZQ_CALSTART_NORM_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x145 0 16 $data 
} 
 
proc mc_ZQ_CALSTART_NORM_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x145 0 16 ] 

    return $rdata 
}

proc mc_ZQ_CALSTART_HIGH_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x145 16 16 $data 
} 
 
proc mc_ZQ_CALSTART_HIGH_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x145 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x146_print {} {
    puts "addr: 0x146"
    #fields
    puts "field_name   :ZQ_CALLATCH_HIGH_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CS_NORM_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x146_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x146 $data
}

proc mc_0x146_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x146]

    return $rdata
}

proc mc_ZQ_CALLATCH_HIGH_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x146 0 16 $data 
} 
 
proc mc_ZQ_CALLATCH_HIGH_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x146 0 16 ] 

    return $rdata 
}

proc mc_ZQ_CS_NORM_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x146 16 16 $data 
} 
 
proc mc_ZQ_CS_NORM_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x146 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x147_print {} {
    puts "addr: 0x147"
    #fields
    puts "field_name   :ZQ_CS_HIGH_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CALSTART_TIMEOUT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x147_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x147 $data
}

proc mc_0x147_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x147]

    return $rdata
}

proc mc_ZQ_CS_HIGH_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x147 0 16 $data 
} 
 
proc mc_ZQ_CS_HIGH_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x147 0 16 ] 

    return $rdata 
}

proc mc_ZQ_CALSTART_TIMEOUT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x147 16 16 $data 
} 
 
proc mc_ZQ_CALSTART_TIMEOUT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x147 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x148_print {} {
    puts "addr: 0x148"
    #fields
    puts "field_name   :ZQ_CALLATCH_TIMEOUT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CS_TIMEOUT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x148_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x148 $data
}

proc mc_0x148_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x148]

    return $rdata
}

proc mc_ZQ_CALLATCH_TIMEOUT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x148 0 16 $data 
} 
 
proc mc_ZQ_CALLATCH_TIMEOUT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x148 0 16 ] 

    return $rdata 
}

proc mc_ZQ_CS_TIMEOUT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x148 16 16 $data 
} 
 
proc mc_ZQ_CS_TIMEOUT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x148 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x149_print {} {
    puts "addr: 0x149"
    #fields
    puts "field_name   :ZQ_PROMOTE_THRESHOLD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :TIMEOUT_TIMER_LOG "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x0 "
} 

proc mc_0x149_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x149 $data
}

proc mc_0x149_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x149]

    return $rdata
}

proc mc_ZQ_PROMOTE_THRESHOLD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x149 0 16 $data 
} 
 
proc mc_ZQ_PROMOTE_THRESHOLD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x149 0 16 ] 

    return $rdata 
}

proc mc_TIMEOUT_TIMER_LOG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x149 16 9 $data 
} 
 
proc mc_TIMEOUT_TIMER_LOG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x149 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x14a_print {} {
    puts "addr: 0x14a"
    #fields
    puts "field_name   :ZQINIT_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0x200 "
    puts "field_name   :ZQCL_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :12 "
    puts "default field_value  :0x100 "
} 

proc mc_0x14a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x14a $data
}

proc mc_0x14a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x14a]

    return $rdata
}

proc mc_ZQINIT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14a 0 12 $data 
} 
 
proc mc_ZQINIT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14a 0 12 ] 

    return $rdata 
}

proc mc_ZQCL_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14a 16 12 $data 
} 
 
proc mc_ZQCL_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14a 16 12 ] 

    return $rdata 
}

#################################

proc mc_0x14b_print {} {
    puts "addr: 0x14b"
    #fields
    puts "field_name   :ZQCS_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0x40 "
    puts "field_name   :TZQCAL_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :12 "
    puts "default field_value  :0xaf2 "
} 

proc mc_0x14b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x14b $data
}

proc mc_0x14b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x14b]

    return $rdata
}

proc mc_ZQCS_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14b 0 12 $data 
} 
 
proc mc_ZQCS_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14b 0 12 ] 

    return $rdata 
}

proc mc_TZQCAL_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14b 16 12 $data 
} 
 
proc mc_TZQCAL_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14b 16 12 ] 

    return $rdata 
}

#################################

proc mc_0x14c_print {} {
    puts "addr: 0x14c"
    #fields
    puts "field_name   :TZQLAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x55 "
    puts "field_name   :ZQINIT_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :12 "
    puts "default field_value  :0x200 "
} 

proc mc_0x14c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x14c $data
}

proc mc_0x14c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x14c]

    return $rdata
}

proc mc_TZQLAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14c 0 7 $data 
} 
 
proc mc_TZQLAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14c 0 7 ] 

    return $rdata 
}

proc mc_ZQINIT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14c 8 12 $data 
} 
 
proc mc_ZQINIT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14c 8 12 ] 

    return $rdata 
}

#################################

proc mc_0x14d_print {} {
    puts "addr: 0x14d"
    #fields
    puts "field_name   :ZQCL_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0x100 "
    puts "field_name   :ZQCS_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :12 "
    puts "default field_value  :0x40 "
} 

proc mc_0x14d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x14d $data
}

proc mc_0x14d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x14d]

    return $rdata
}

proc mc_ZQCL_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14d 0 12 $data 
} 
 
proc mc_ZQCL_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14d 0 12 ] 

    return $rdata 
}

proc mc_ZQCS_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14d 16 12 $data 
} 
 
proc mc_ZQCS_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14d 16 12 ] 

    return $rdata 
}

#################################

proc mc_0x14e_print {} {
    puts "addr: 0x14e"
    #fields
    puts "field_name   :TZQCAL_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :12 "
    puts "default field_value  :0xaf2 "
    puts "field_name   :TZQLAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :7 "
    puts "default field_value  :0x55 "
    puts "field_name   :ZQ_SW_REQ_START_LATCH_MAP "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x14e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x14e $data
}

proc mc_0x14e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x14e]

    return $rdata
}

proc mc_TZQCAL_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14e 0 12 $data 
} 
 
proc mc_TZQCAL_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14e 0 12 ] 

    return $rdata 
}

proc mc_TZQLAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14e 16 7 $data 
} 
 
proc mc_TZQLAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14e 16 7 ] 

    return $rdata 
}

proc mc_ZQ_SW_REQ_START_LATCH_MAP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14e 24 2 $data 
} 
 
proc mc_ZQ_SW_REQ_START_LATCH_MAP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14e 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x14f_print {} {
    puts "addr: 0x14f"
    #fields
    puts "field_name   :ZQ_REQ "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_REQ_PENDING "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQCS_ROTATE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :ZQ_CAL_START_MAP_0 "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x14f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x14f $data
}

proc mc_0x14f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x14f]

    return $rdata
}

proc mc_ZQ_REQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14f 0 4 $data 
} 
 
proc mc_ZQ_REQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14f 0 4 ] 

    return $rdata 
}

proc mc_ZQ_REQ_PENDING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14f 8 1 $data 
} 
 
proc mc_ZQ_REQ_PENDING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14f 8 1 ] 

    return $rdata 
}

proc mc_ZQCS_ROTATE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14f 16 1 $data 
} 
 
proc mc_ZQCS_ROTATE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14f 16 1 ] 

    return $rdata 
}

proc mc_ZQ_CAL_START_MAP_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x14f 24 2 $data 
} 
 
proc mc_ZQ_CAL_START_MAP_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x14f 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x150_print {} {
    puts "addr: 0x150"
    #fields
    puts "field_name   :ZQ_CAL_LATCH_MAP_0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CAL_START_MAP_1 "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :ZQ_CAL_LATCH_MAP_1 "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :BANK_DIFF_0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x150_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x150 $data
}

proc mc_0x150_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x150]

    return $rdata
}

proc mc_ZQ_CAL_LATCH_MAP_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x150 0 2 $data 
} 
 
proc mc_ZQ_CAL_LATCH_MAP_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x150 0 2 ] 

    return $rdata 
}

proc mc_ZQ_CAL_START_MAP_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x150 8 2 $data 
} 
 
proc mc_ZQ_CAL_START_MAP_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x150 8 2 ] 

    return $rdata 
}

proc mc_ZQ_CAL_LATCH_MAP_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x150 16 2 $data 
} 
 
proc mc_ZQ_CAL_LATCH_MAP_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x150 16 2 ] 

    return $rdata 
}

proc mc_BANK_DIFF_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x150 24 2 $data 
} 
 
proc mc_BANK_DIFF_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x150 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x151_print {} {
    puts "addr: 0x151"
    #fields
    puts "field_name   :BANK_DIFF_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :ROW_DIFF_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x2 "
    puts "field_name   :ROW_DIFF_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x2 "
    puts "field_name   :COL_DIFF_0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
} 

proc mc_0x151_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x151 $data
}

proc mc_0x151_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x151]

    return $rdata
}

proc mc_BANK_DIFF_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x151 0 2 $data 
} 
 
proc mc_BANK_DIFF_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x151 0 2 ] 

    return $rdata 
}

proc mc_ROW_DIFF_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x151 8 3 $data 
} 
 
proc mc_ROW_DIFF_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x151 8 3 ] 

    return $rdata 
}

proc mc_ROW_DIFF_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x151 16 3 $data 
} 
 
proc mc_ROW_DIFF_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x151 16 3 ] 

    return $rdata 
}

proc mc_COL_DIFF_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x151 24 4 $data 
} 
 
proc mc_COL_DIFF_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x151 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x152_print {} {
    puts "addr: 0x152"
    #fields
    puts "field_name   :COL_DIFF_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :BG_DIFF_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :BG_DIFF_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x152_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x152 $data
}

proc mc_0x152_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x152]

    return $rdata
}

proc mc_COL_DIFF_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x152 0 4 $data 
} 
 
proc mc_COL_DIFF_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x152 0 4 ] 

    return $rdata 
}

proc mc_BG_DIFF_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x152 8 2 $data 
} 
 
proc mc_BG_DIFF_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x152 8 2 ] 

    return $rdata 
}

proc mc_BG_DIFF_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x152 16 2 $data 
} 
 
proc mc_BG_DIFF_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x152 16 2 ] 

    return $rdata 
}

#################################

proc mc_0x153_print {} {
    puts "addr: 0x153"
    #fields
    puts "field_name   :CS_VAL_LOWER_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :CS_VAL_UPPER_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x7ff "
} 

proc mc_0x153_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x153 $data
}

proc mc_0x153_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x153]

    return $rdata
}

proc mc_CS_VAL_LOWER_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x153 0 16 $data 
} 
 
proc mc_CS_VAL_LOWER_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x153 0 16 ] 

    return $rdata 
}

proc mc_CS_VAL_UPPER_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x153 16 16 $data 
} 
 
proc mc_CS_VAL_UPPER_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x153 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x154_print {} {
    puts "addr: 0x154"
    #fields
    puts "field_name   :ROW_START_VAL_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :CS_MSK_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x1ff "
} 

proc mc_0x154_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x154 $data
}

proc mc_0x154_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x154]

    return $rdata
}

proc mc_ROW_START_VAL_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x154 0 2 $data 
} 
 
proc mc_ROW_START_VAL_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x154 0 2 ] 

    return $rdata 
}

proc mc_CS_MSK_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x154 8 16 $data 
} 
 
proc mc_CS_MSK_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x154 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x155_print {} {
    puts "addr: 0x155"
    #fields
    puts "field_name   :CS_VAL_LOWER_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x800 "
    puts "field_name   :CS_VAL_UPPER_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0xfff "
} 

proc mc_0x155_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x155 $data
}

proc mc_0x155_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x155]

    return $rdata
}

proc mc_CS_VAL_LOWER_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x155 0 16 $data 
} 
 
proc mc_CS_VAL_LOWER_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x155 0 16 ] 

    return $rdata 
}

proc mc_CS_VAL_UPPER_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x155 16 16 $data 
} 
 
proc mc_CS_VAL_UPPER_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x155 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x156_print {} {
    puts "addr: 0x156"
    #fields
    puts "field_name   :ROW_START_VAL_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :CS_MSK_1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0x1ff "
    puts "field_name   :CS_MAP_NON_POW2 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x156_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x156 $data
}

proc mc_0x156_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x156]

    return $rdata
}

proc mc_ROW_START_VAL_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x156 0 2 $data 
} 
 
proc mc_ROW_START_VAL_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x156 0 2 ] 

    return $rdata 
}

proc mc_CS_MSK_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x156 8 16 $data 
} 
 
proc mc_CS_MSK_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x156 8 16 ] 

    return $rdata 
}

proc mc_CS_MAP_NON_POW2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x156 24 2 $data 
} 
 
proc mc_CS_MAP_NON_POW2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x156 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x157_print {} {
    puts "addr: 0x157"
    #fields
    puts "field_name   :PROGRAMMABLE_ADDRESS_ORDER "
    puts "field_access :RW+ "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :BANK_START_BIT "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
    puts "field_name   :APREBIT "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x18 "
    puts "field_name   :AGE_COUNT "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0xff "
} 

proc mc_0x157_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x157 $data
}

proc mc_0x157_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x157]

    return $rdata
}

proc mc_PROGRAMMABLE_ADDRESS_ORDER_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x157 0 4 $data 
} 
 
proc mc_PROGRAMMABLE_ADDRESS_ORDER_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x157 0 4 ] 

    return $rdata 
}

proc mc_BANK_START_BIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x157 8 5 $data 
} 
 
proc mc_BANK_START_BIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x157 8 5 ] 

    return $rdata 
}

proc mc_APREBIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x157 16 5 $data 
} 
 
proc mc_APREBIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x157 16 5 ] 

    return $rdata 
}

proc mc_AGE_COUNT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x157 24 8 $data 
} 
 
proc mc_AGE_COUNT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x157 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x158_print {} {
    puts "addr: 0x158"
    #fields
    puts "field_name   :COMMAND_AGE_COUNT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0xff "
    puts "field_name   :ADDR_CMP_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :ADDR_COLLISION_MPM_DIS "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :BANK_SPLIT_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x158_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x158 $data
}

proc mc_0x158_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x158]

    return $rdata
}

proc mc_COMMAND_AGE_COUNT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x158 0 8 $data 
} 
 
proc mc_COMMAND_AGE_COUNT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x158 0 8 ] 

    return $rdata 
}

proc mc_ADDR_CMP_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x158 8 1 $data 
} 
 
proc mc_ADDR_CMP_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x158 8 1 ] 

    return $rdata 
}

proc mc_ADDR_COLLISION_MPM_DIS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x158 16 1 $data 
} 
 
proc mc_ADDR_COLLISION_MPM_DIS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x158 16 1 ] 

    return $rdata 
}

proc mc_BANK_SPLIT_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x158 24 1 $data 
} 
 
proc mc_BANK_SPLIT_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x158 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x159_print {} {
    puts "addr: 0x159"
    #fields
    puts "field_name   :PLACEMENT_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :PRIORITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :RW_SAME_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :RW_SAME_PAGE_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x159_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x159 $data
}

proc mc_0x159_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x159]

    return $rdata
}

proc mc_PLACEMENT_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x159 0 1 $data 
} 
 
proc mc_PLACEMENT_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x159 0 1 ] 

    return $rdata 
}

proc mc_PRIORITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x159 8 1 $data 
} 
 
proc mc_PRIORITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x159 8 1 ] 

    return $rdata 
}

proc mc_RW_SAME_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x159 16 1 $data 
} 
 
proc mc_RW_SAME_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x159 16 1 ] 

    return $rdata 
}

proc mc_RW_SAME_PAGE_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x159 24 1 $data 
} 
 
proc mc_RW_SAME_PAGE_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x159 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x15a_print {} {
    puts "addr: 0x15a"
    #fields
    puts "field_name   :CS_SAME_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :W2R_SPLIT_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :DISABLE_RW_GROUP_W_BNK_CONFLICT "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x1 "
    puts "field_name   :NUM_Q_ENTRIES_ACT_DISABLE "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
} 

proc mc_0x15a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x15a $data
}

proc mc_0x15a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x15a]

    return $rdata
}

proc mc_CS_SAME_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15a 0 1 $data 
} 
 
proc mc_CS_SAME_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15a 0 1 ] 

    return $rdata 
}

proc mc_W2R_SPLIT_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15a 8 1 $data 
} 
 
proc mc_W2R_SPLIT_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15a 8 1 ] 

    return $rdata 
}

proc mc_DISABLE_RW_GROUP_W_BNK_CONFLICT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15a 16 2 $data 
} 
 
proc mc_DISABLE_RW_GROUP_W_BNK_CONFLICT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15a 16 2 ] 

    return $rdata 
}

proc mc_NUM_Q_ENTRIES_ACT_DISABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15a 24 4 $data 
} 
 
proc mc_NUM_Q_ENTRIES_ACT_DISABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15a 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x15b_print {} {
    puts "addr: 0x15b"
    #fields
    puts "field_name   :DISABLE_RD_INTERLEAVE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :SWAP_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :INHIBIT_DRAM_CMD "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :CS_MAP "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x1 "
} 

proc mc_0x15b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x15b $data
}

proc mc_0x15b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x15b]

    return $rdata
}

proc mc_DISABLE_RD_INTERLEAVE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15b 0 1 $data 
} 
 
proc mc_DISABLE_RD_INTERLEAVE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15b 0 1 ] 

    return $rdata 
}

proc mc_SWAP_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15b 8 1 $data 
} 
 
proc mc_SWAP_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15b 8 1 ] 

    return $rdata 
}

proc mc_INHIBIT_DRAM_CMD_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15b 16 2 $data 
} 
 
proc mc_INHIBIT_DRAM_CMD_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15b 16 2 ] 

    return $rdata 
}

proc mc_CS_MAP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15b 24 2 $data 
} 
 
proc mc_CS_MAP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15b 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x15c_print {} {
    puts "addr: 0x15c"
    #fields
    puts "field_name   :BURST_ON_FLY_BIT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0xc "
    puts "field_name   :MEM_DP_REDUCTION "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :WRITE_ADDR_CHAN_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :WRITE_DATA_CHAN_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x15c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x15c $data
}

proc mc_0x15c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x15c]

    return $rdata
}

proc mc_BURST_ON_FLY_BIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15c 0 4 $data 
} 
 
proc mc_BURST_ON_FLY_BIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15c 0 4 ] 

    return $rdata 
}

proc mc_MEM_DP_REDUCTION_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15c 8 1 $data 
} 
 
proc mc_MEM_DP_REDUCTION_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15c 8 1 ] 

    return $rdata 
}

proc mc_WRITE_ADDR_CHAN_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15c 16 1 $data 
} 
 
proc mc_WRITE_ADDR_CHAN_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15c 16 1 ] 

    return $rdata 
}

proc mc_WRITE_DATA_CHAN_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15c 24 2 $data 
} 
 
proc mc_WRITE_DATA_CHAN_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15c 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x15d_print {} {
    puts "addr: 0x15d"
    #fields
    puts "field_name   :WRITE_RESP_CHAN_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :READ_ADDR_CHAN_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :READ_DATA_CHAN_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x15d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x15d $data
}

proc mc_0x15d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x15d]

    return $rdata
}

proc mc_WRITE_RESP_CHAN_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15d 0 1 $data 
} 
 
proc mc_WRITE_RESP_CHAN_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15d 0 1 ] 

    return $rdata 
}

proc mc_READ_ADDR_CHAN_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15d 8 1 $data 
} 
 
proc mc_READ_ADDR_CHAN_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15d 8 1 ] 

    return $rdata 
}

proc mc_READ_DATA_CHAN_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15d 16 1 $data 
} 
 
proc mc_READ_DATA_CHAN_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15d 16 1 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15d 24 1 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15d 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x15e_print {} {
    puts "addr: 0x15e"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :WRITE_PARITY_ERR_BRESP_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :READ_PARITY_ERR_RRESP_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :WRITE_ADDR_CHAN_TRIGGER_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x15e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x15e $data
}

proc mc_0x15e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x15e]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15e 0 1 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15e 0 1 ] 

    return $rdata 
}

proc mc_WRITE_PARITY_ERR_BRESP_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15e 8 1 $data 
} 
 
proc mc_WRITE_PARITY_ERR_BRESP_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15e 8 1 ] 

    return $rdata 
}

proc mc_READ_PARITY_ERR_RRESP_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15e 16 1 $data 
} 
 
proc mc_READ_PARITY_ERR_RRESP_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15e 16 1 ] 

    return $rdata 
}

proc mc_WRITE_ADDR_CHAN_TRIGGER_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15e 24 1 $data 
} 
 
proc mc_WRITE_ADDR_CHAN_TRIGGER_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15e 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x15f_print {} {
    puts "addr: 0x15f"
    #fields
    puts "field_name   :WRITE_DATA_CHAN_TRIGGER_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :WRITE_RESP_CHAN_CORRUPT_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :READ_ADDR_CHAN_TRIGGER_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :READ_DATA_CHAN_CORRUPT_PARITY_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x15f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x15f $data
}

proc mc_0x15f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x15f]

    return $rdata
}

proc mc_WRITE_DATA_CHAN_TRIGGER_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15f 0 1 $data 
} 
 
proc mc_WRITE_DATA_CHAN_TRIGGER_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15f 0 1 ] 

    return $rdata 
}

proc mc_WRITE_RESP_CHAN_CORRUPT_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15f 8 1 $data 
} 
 
proc mc_WRITE_RESP_CHAN_CORRUPT_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15f 8 1 ] 

    return $rdata 
}

proc mc_READ_ADDR_CHAN_TRIGGER_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15f 16 1 $data 
} 
 
proc mc_READ_ADDR_CHAN_TRIGGER_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15f 16 1 ] 

    return $rdata 
}

proc mc_READ_DATA_CHAN_CORRUPT_PARITY_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x15f 24 1 $data 
} 
 
proc mc_READ_DATA_CHAN_CORRUPT_PARITY_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x15f 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x160_print {} {
    puts "addr: 0x160"
    #fields
    puts "field_name   :ECC_AXI_ERROR_RESPONSE_INHIBIT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :WRITE_PARITY_ERR_CORRUPT_ECC_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :ENHANCED_PARITY_PROTECTION_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :MEMDATA_RATIO_0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x3 "
} 

proc mc_0x160_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x160 $data
}

proc mc_0x160_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x160]

    return $rdata
}

proc mc_ECC_AXI_ERROR_RESPONSE_INHIBIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x160 0 1 $data 
} 
 
proc mc_ECC_AXI_ERROR_RESPONSE_INHIBIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x160 0 1 ] 

    return $rdata 
}

proc mc_WRITE_PARITY_ERR_CORRUPT_ECC_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x160 8 1 $data 
} 
 
proc mc_WRITE_PARITY_ERR_CORRUPT_ECC_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x160 8 1 ] 

    return $rdata 
}

proc mc_ENHANCED_PARITY_PROTECTION_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x160 16 1 $data 
} 
 
proc mc_ENHANCED_PARITY_PROTECTION_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x160 16 1 ] 

    return $rdata 
}

proc mc_MEMDATA_RATIO_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x160 24 3 $data 
} 
 
proc mc_MEMDATA_RATIO_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x160 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x161_print {} {
    puts "addr: 0x161"
    #fields
    puts "field_name   :MEMDATA_RATIO_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x3 "
} 

proc mc_0x161_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x161 $data
}

proc mc_0x161_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x161]

    return $rdata
}

proc mc_MEMDATA_RATIO_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x161 0 3 $data 
} 
 
proc mc_MEMDATA_RATIO_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x161 0 3 ] 

    return $rdata 
}

#################################

proc mc_0x184_print {} {
    puts "addr: 0x184"
    #fields
    puts "field_name   :Q_FULLNESS "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
} 

proc mc_0x184_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x184 $data
}

proc mc_0x184_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x184]

    return $rdata
}

proc mc_Q_FULLNESS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x184 24 4 $data 
} 
 
proc mc_Q_FULLNESS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x184 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x185_print {} {
    puts "addr: 0x185"
    #fields
    puts "field_name   :IN_ORDER_ACCEPT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :WR_ORDER_REQ "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :CONTROLLER_BUSY "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :CTRLUPD_REQ "
    puts "field_access :WR "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x185_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x185 $data
}

proc mc_0x185_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x185]

    return $rdata
}

proc mc_IN_ORDER_ACCEPT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x185 0 1 $data 
} 
 
proc mc_IN_ORDER_ACCEPT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x185 0 1 ] 

    return $rdata 
}

proc mc_WR_ORDER_REQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x185 8 2 $data 
} 
 
proc mc_WR_ORDER_REQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x185 8 2 ] 

    return $rdata 
}

proc mc_CONTROLLER_BUSY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x185 16 1 $data 
} 
 
proc mc_CONTROLLER_BUSY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x185 16 1 ] 

    return $rdata 
}

proc mc_CTRLUPD_REQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x185 24 1 $data 
} 
 
proc mc_CTRLUPD_REQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x185 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x186_print {} {
    puts "addr: 0x186"
    #fields
    puts "field_name   :RD_PREAMBLE_LEN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :WR_PREAMBLE_LEN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x1 "
    puts "field_name   :RD_PREAMBLE_LEN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :WR_PREAMBLE_LEN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x1 "
} 

proc mc_0x186_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x186 $data
}

proc mc_0x186_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x186]

    return $rdata
}

proc mc_RD_PREAMBLE_LEN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x186 0 8 $data 
} 
 
proc mc_RD_PREAMBLE_LEN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x186 0 8 ] 

    return $rdata 
}

proc mc_WR_PREAMBLE_LEN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x186 8 8 $data 
} 
 
proc mc_WR_PREAMBLE_LEN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x186 8 8 ] 

    return $rdata 
}

proc mc_RD_PREAMBLE_LEN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x186 16 8 $data 
} 
 
proc mc_RD_PREAMBLE_LEN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x186 16 8 ] 

    return $rdata 
}

proc mc_WR_PREAMBLE_LEN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x186 24 8 $data 
} 
 
proc mc_WR_PREAMBLE_LEN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x186 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x187_print {} {
    puts "addr: 0x187"
    #fields
    puts "field_name   :RD_PREAMBLE_TRAINING_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :WR_DBI_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :RD_DBI_EN "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x187_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x187 $data
}

proc mc_0x187_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x187]

    return $rdata
}

proc mc_RD_PREAMBLE_TRAINING_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x187 0 1 $data 
} 
 
proc mc_RD_PREAMBLE_TRAINING_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x187 0 1 ] 

    return $rdata 
}

proc mc_WR_DBI_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x187 8 1 $data 
} 
 
proc mc_WR_DBI_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x187 8 1 ] 

    return $rdata 
}

proc mc_RD_DBI_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x187 16 1 $data 
} 
 
proc mc_RD_DBI_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x187 16 1 ] 

    return $rdata 
}

#################################

proc mc_0x188_print {} {
    puts "addr: 0x188"
    #fields
    puts "field_name   :DFI_ERROR "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :10 "
    puts "default field_value  :0x0 "
} 

proc mc_0x188_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x188 $data
}

proc mc_0x188_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x188]

    return $rdata
}

proc mc_DFI_ERROR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x188 0 10 $data 
} 
 
proc mc_DFI_ERROR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x188 0 10 ] 

    return $rdata 
}

#################################

proc mc_0x189_print {} {
    puts "addr: 0x189"
    #fields
    puts "field_name   :DFI_ERROR_INFO_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x189_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x189 $data
}

proc mc_0x189_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x189]

    return $rdata
}

proc mc_DFI_ERROR_INFO_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x189 0 32 $data 
} 
 
proc mc_DFI_ERROR_INFO_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x189 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x18a_print {} {
    puts "addr: 0x18a"
    #fields
    puts "field_name   :DFI_ERROR_INFO_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :BG_ROTATE_EN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x2 "
    puts "field_name   :RESERVED "
    puts "field_access :WR "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :DFI_RD_FIFO_RESYNC_EN "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x18a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x18a $data
}

proc mc_0x18a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x18a]

    return $rdata
}

proc mc_DFI_ERROR_INFO_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18a 0 8 $data 
} 
 
proc mc_DFI_ERROR_INFO_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18a 0 8 ] 

    return $rdata 
}

proc mc_BG_ROTATE_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18a 8 2 $data 
} 
 
proc mc_BG_ROTATE_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18a 8 2 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18a 16 1 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18a 16 1 ] 

    return $rdata 
}

proc mc_DFI_RD_FIFO_RESYNC_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18a 24 1 $data 
} 
 
proc mc_DFI_RD_FIFO_RESYNC_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18a 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x18b_print {} {
    puts "addr: 0x18b"
    #fields
    puts "field_name   :POSTAMBLE_SUPPORT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x18b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x18b $data
}

proc mc_0x18b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x18b]

    return $rdata
}

proc mc_POSTAMBLE_SUPPORT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18b 0 2 $data 
} 
 
proc mc_POSTAMBLE_SUPPORT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18b 0 2 ] 

    return $rdata 
}

#################################

proc mc_0x18c_print {} {
    puts "addr: 0x18c"
    #fields
    puts "field_name   :INT_STATUS_MASTER "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x18c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x18c $data
}

proc mc_0x18c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x18c]

    return $rdata
}

proc mc_INT_STATUS_MASTER_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18c 0 32 $data 
} 
 
proc mc_INT_STATUS_MASTER_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x18d_print {} {
    puts "addr: 0x18d"
    #fields
    puts "field_name   :INT_MASK_MASTER "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x18d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x18d $data
}

proc mc_0x18d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x18d]

    return $rdata
}

proc mc_INT_MASK_MASTER_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18d 0 32 $data 
} 
 
proc mc_INT_MASK_MASTER_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x18e_print {} {
    puts "addr: 0x18e"
    #fields
    puts "field_name   :INT_STATUS_TIMEOUT "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x18e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x18e $data
}

proc mc_0x18e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x18e]

    return $rdata
}

proc mc_INT_STATUS_TIMEOUT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18e 0 32 $data 
} 
 
proc mc_INT_STATUS_TIMEOUT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x18f_print {} {
    puts "addr: 0x18f"
    #fields
    puts "field_name   :INT_STATUS_ECC "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x18f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x18f $data
}

proc mc_0x18f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x18f]

    return $rdata
}

proc mc_INT_STATUS_ECC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x18f 0 32 $data 
} 
 
proc mc_INT_STATUS_ECC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x18f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x190_print {} {
    puts "addr: 0x190"
    #fields
    puts "field_name   :INT_STATUS_LOWPOWER "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x190_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x190 $data
}

proc mc_0x190_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x190]

    return $rdata
}

proc mc_INT_STATUS_LOWPOWER_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x190 0 16 $data 
} 
 
proc mc_INT_STATUS_LOWPOWER_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x190 0 16 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x190 16 16 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x190 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x191_print {} {
    puts "addr: 0x191"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x191_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x191 $data
}

proc mc_0x191_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x191]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x191 0 16 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x191 0 16 ] 

    return $rdata 
}

#################################

proc mc_0x192_print {} {
    puts "addr: 0x192"
    #fields
    puts "field_name   :INT_STATUS_TRAINING "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x192_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x192 $data
}

proc mc_0x192_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x192]

    return $rdata
}

proc mc_INT_STATUS_TRAINING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x192 0 32 $data 
} 
 
proc mc_INT_STATUS_TRAINING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x192 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x193_print {} {
    puts "addr: 0x193"
    #fields
    puts "field_name   :INT_STATUS_USERIF "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x193_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x193 $data
}

proc mc_0x193_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x193]

    return $rdata
}

proc mc_INT_STATUS_USERIF_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x193 0 32 $data 
} 
 
proc mc_INT_STATUS_USERIF_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x193 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x194_print {} {
    puts "addr: 0x194"
    #fields
    puts "field_name   :INT_STATUS_MISC "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_STATUS_BIST "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_STATUS_CRC "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x194_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x194 $data
}

proc mc_0x194_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x194]

    return $rdata
}

proc mc_INT_STATUS_MISC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x194 0 16 $data 
} 
 
proc mc_INT_STATUS_MISC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x194 0 16 ] 

    return $rdata 
}

proc mc_INT_STATUS_BIST_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x194 16 8 $data 
} 
 
proc mc_INT_STATUS_BIST_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x194 16 8 ] 

    return $rdata 
}

proc mc_INT_STATUS_CRC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x194 24 8 $data 
} 
 
proc mc_INT_STATUS_CRC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x194 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x195_print {} {
    puts "addr: 0x195"
    #fields
    puts "field_name   :INT_STATUS_DFI "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_STATUS_DIMM "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_STATUS_FREQ "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_STATUS_INIT "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x195_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x195 $data
}

proc mc_0x195_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x195]

    return $rdata
}

proc mc_INT_STATUS_DFI_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x195 0 8 $data 
} 
 
proc mc_INT_STATUS_DFI_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x195 0 8 ] 

    return $rdata 
}

proc mc_INT_STATUS_DIMM_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x195 8 8 $data 
} 
 
proc mc_INT_STATUS_DIMM_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x195 8 8 ] 

    return $rdata 
}

proc mc_INT_STATUS_FREQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x195 16 8 $data 
} 
 
proc mc_INT_STATUS_FREQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x195 16 8 ] 

    return $rdata 
}

proc mc_INT_STATUS_INIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x195 24 8 $data 
} 
 
proc mc_INT_STATUS_INIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x195 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x196_print {} {
    puts "addr: 0x196"
    #fields
    puts "field_name   :INT_STATUS_MODE "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_STATUS_PARITY "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x196_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x196 $data
}

proc mc_0x196_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x196]

    return $rdata
}

proc mc_INT_STATUS_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x196 0 8 $data 
} 
 
proc mc_INT_STATUS_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x196 0 8 ] 

    return $rdata 
}

proc mc_INT_STATUS_PARITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x196 8 8 $data 
} 
 
proc mc_INT_STATUS_PARITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x196 8 8 ] 

    return $rdata 
}

#################################

proc mc_0x197_print {} {
    puts "addr: 0x197"
    #fields
    puts "field_name   :INT_ACK_TIMEOUT "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x197_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x197 $data
}

proc mc_0x197_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x197]

    return $rdata
}

proc mc_INT_ACK_TIMEOUT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x197 0 32 $data 
} 
 
proc mc_INT_ACK_TIMEOUT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x197 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x198_print {} {
    puts "addr: 0x198"
    #fields
    puts "field_name   :INT_ACK_ECC "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x198_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x198 $data
}

proc mc_0x198_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x198]

    return $rdata
}

proc mc_INT_ACK_ECC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x198 0 32 $data 
} 
 
proc mc_INT_ACK_ECC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x198 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x199_print {} {
    puts "addr: 0x199"
    #fields
    puts "field_name   :INT_ACK_LOWPOWER "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :WR "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x199_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x199 $data
}

proc mc_0x199_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x199]

    return $rdata
}

proc mc_INT_ACK_LOWPOWER_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x199 0 16 $data 
} 
 
proc mc_INT_ACK_LOWPOWER_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x199 0 16 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x199 16 16 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x199 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x19a_print {} {
    puts "addr: 0x19a"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x19a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x19a $data
}

proc mc_0x19a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x19a]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19a 0 16 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19a 0 16 ] 

    return $rdata 
}

#################################

proc mc_0x19b_print {} {
    puts "addr: 0x19b"
    #fields
    puts "field_name   :INT_ACK_TRAINING "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x19b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x19b $data
}

proc mc_0x19b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x19b]

    return $rdata
}

proc mc_INT_ACK_TRAINING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19b 0 32 $data 
} 
 
proc mc_INT_ACK_TRAINING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x19c_print {} {
    puts "addr: 0x19c"
    #fields
    puts "field_name   :INT_ACK_USERIF "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x19c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x19c $data
}

proc mc_0x19c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x19c]

    return $rdata
}

proc mc_INT_ACK_USERIF_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19c 0 32 $data 
} 
 
proc mc_INT_ACK_USERIF_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x19d_print {} {
    puts "addr: 0x19d"
    #fields
    puts "field_name   :INT_ACK_MISC "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_ACK_BIST "
    puts "field_access :WR "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_ACK_CRC "
    puts "field_access :WR "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x19d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x19d $data
}

proc mc_0x19d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x19d]

    return $rdata
}

proc mc_INT_ACK_MISC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19d 0 16 $data 
} 
 
proc mc_INT_ACK_MISC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19d 0 16 ] 

    return $rdata 
}

proc mc_INT_ACK_BIST_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19d 16 8 $data 
} 
 
proc mc_INT_ACK_BIST_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19d 16 8 ] 

    return $rdata 
}

proc mc_INT_ACK_CRC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19d 24 8 $data 
} 
 
proc mc_INT_ACK_CRC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19d 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x19e_print {} {
    puts "addr: 0x19e"
    #fields
    puts "field_name   :INT_ACK_DFI "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_ACK_DIMM "
    puts "field_access :WR "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_ACK_FREQ "
    puts "field_access :WR "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_ACK_INIT "
    puts "field_access :WR "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x19e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x19e $data
}

proc mc_0x19e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x19e]

    return $rdata
}

proc mc_INT_ACK_DFI_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19e 0 8 $data 
} 
 
proc mc_INT_ACK_DFI_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19e 0 8 ] 

    return $rdata 
}

proc mc_INT_ACK_DIMM_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19e 8 8 $data 
} 
 
proc mc_INT_ACK_DIMM_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19e 8 8 ] 

    return $rdata 
}

proc mc_INT_ACK_FREQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19e 16 8 $data 
} 
 
proc mc_INT_ACK_FREQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19e 16 8 ] 

    return $rdata 
}

proc mc_INT_ACK_INIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19e 24 8 $data 
} 
 
proc mc_INT_ACK_INIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19e 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x19f_print {} {
    puts "addr: 0x19f"
    #fields
    puts "field_name   :INT_ACK_MODE "
    puts "field_access :WR "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_ACK_PARITY "
    puts "field_access :WR "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x19f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x19f $data
}

proc mc_0x19f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x19f]

    return $rdata
}

proc mc_INT_ACK_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19f 0 8 $data 
} 
 
proc mc_INT_ACK_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19f 0 8 ] 

    return $rdata 
}

proc mc_INT_ACK_PARITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x19f 8 8 $data 
} 
 
proc mc_INT_ACK_PARITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x19f 8 8 ] 

    return $rdata 
}

#################################

proc mc_0x1a0_print {} {
    puts "addr: 0x1a0"
    #fields
    puts "field_name   :INT_MASK_TIMEOUT "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a0 $data
}

proc mc_0x1a0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a0]

    return $rdata
}

proc mc_INT_MASK_TIMEOUT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a0 0 32 $data 
} 
 
proc mc_INT_MASK_TIMEOUT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a0 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1a1_print {} {
    puts "addr: 0x1a1"
    #fields
    puts "field_name   :INT_MASK_ECC "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a1 $data
}

proc mc_0x1a1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a1]

    return $rdata
}

proc mc_INT_MASK_ECC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a1 0 32 $data 
} 
 
proc mc_INT_MASK_ECC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a1 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1a2_print {} {
    puts "addr: 0x1a2"
    #fields
    puts "field_name   :INT_MASK_LOWPOWER "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a2 $data
}

proc mc_0x1a2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a2]

    return $rdata
}

proc mc_INT_MASK_LOWPOWER_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a2 0 16 $data 
} 
 
proc mc_INT_MASK_LOWPOWER_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a2 0 16 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a2 16 16 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a2 16 16 ] 

    return $rdata 
}

#################################

proc mc_0x1a3_print {} {
    puts "addr: 0x1a3"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a3 $data
}

proc mc_0x1a3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a3]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a3 0 16 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a3 0 16 ] 

    return $rdata 
}

#################################

proc mc_0x1a4_print {} {
    puts "addr: 0x1a4"
    #fields
    puts "field_name   :INT_MASK_TRAINING "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a4 $data
}

proc mc_0x1a4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a4]

    return $rdata
}

proc mc_INT_MASK_TRAINING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a4 0 32 $data 
} 
 
proc mc_INT_MASK_TRAINING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a4 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1a5_print {} {
    puts "addr: 0x1a5"
    #fields
    puts "field_name   :INT_MASK_USERIF "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a5 $data
}

proc mc_0x1a5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a5]

    return $rdata
}

proc mc_INT_MASK_USERIF_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a5 0 32 $data 
} 
 
proc mc_INT_MASK_USERIF_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a5 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1a6_print {} {
    puts "addr: 0x1a6"
    #fields
    puts "field_name   :INT_MASK_MISC "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_MASK_BIST "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_MASK_CRC "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a6 $data
}

proc mc_0x1a6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a6]

    return $rdata
}

proc mc_INT_MASK_MISC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a6 0 16 $data 
} 
 
proc mc_INT_MASK_MISC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a6 0 16 ] 

    return $rdata 
}

proc mc_INT_MASK_BIST_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a6 16 8 $data 
} 
 
proc mc_INT_MASK_BIST_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a6 16 8 ] 

    return $rdata 
}

proc mc_INT_MASK_CRC_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a6 24 8 $data 
} 
 
proc mc_INT_MASK_CRC_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a6 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x1a7_print {} {
    puts "addr: 0x1a7"
    #fields
    puts "field_name   :INT_MASK_DFI "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_MASK_DIMM "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_MASK_FREQ "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_MASK_INIT "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a7 $data
}

proc mc_0x1a7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a7]

    return $rdata
}

proc mc_INT_MASK_DFI_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a7 0 8 $data 
} 
 
proc mc_INT_MASK_DFI_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a7 0 8 ] 

    return $rdata 
}

proc mc_INT_MASK_DIMM_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a7 8 8 $data 
} 
 
proc mc_INT_MASK_DIMM_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a7 8 8 ] 

    return $rdata 
}

proc mc_INT_MASK_FREQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a7 16 8 $data 
} 
 
proc mc_INT_MASK_FREQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a7 16 8 ] 

    return $rdata 
}

proc mc_INT_MASK_INIT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a7 24 8 $data 
} 
 
proc mc_INT_MASK_INIT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a7 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x1a8_print {} {
    puts "addr: 0x1a8"
    #fields
    puts "field_name   :INT_MASK_MODE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :INT_MASK_PARITY "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a8 $data
}

proc mc_0x1a8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a8]

    return $rdata
}

proc mc_INT_MASK_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a8 0 8 $data 
} 
 
proc mc_INT_MASK_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a8 0 8 ] 

    return $rdata 
}

proc mc_INT_MASK_PARITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a8 8 8 $data 
} 
 
proc mc_INT_MASK_PARITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a8 8 8 ] 

    return $rdata 
}

#################################

proc mc_0x1a9_print {} {
    puts "addr: 0x1a9"
    #fields
    puts "field_name   :OUT_OF_RANGE_ADDR_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1a9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1a9 $data
}

proc mc_0x1a9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1a9]

    return $rdata
}

proc mc_OUT_OF_RANGE_ADDR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1a9 0 32 $data 
} 
 
proc mc_OUT_OF_RANGE_ADDR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1a9 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1aa_print {} {
    puts "addr: 0x1aa"
    #fields
    puts "field_name   :OUT_OF_RANGE_ADDR_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :OUT_OF_RANGE_LENGTH "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :13 "
    puts "default field_value  :0x0 "
    puts "field_name   :OUT_OF_RANGE_TYPE "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1aa_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1aa $data
}

proc mc_0x1aa_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1aa]

    return $rdata
}

proc mc_OUT_OF_RANGE_ADDR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1aa 0 7 $data 
} 
 
proc mc_OUT_OF_RANGE_ADDR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1aa 0 7 ] 

    return $rdata 
}

proc mc_OUT_OF_RANGE_LENGTH_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1aa 8 13 $data 
} 
 
proc mc_OUT_OF_RANGE_LENGTH_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1aa 8 13 ] 

    return $rdata 
}

proc mc_OUT_OF_RANGE_TYPE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1aa 24 7 $data 
} 
 
proc mc_OUT_OF_RANGE_TYPE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1aa 24 7 ] 

    return $rdata 
}

#################################

proc mc_0x1ab_print {} {
    puts "addr: 0x1ab"
    #fields
    puts "field_name   :OUT_OF_RANGE_SOURCE_ID "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :15 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1ab_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ab $data
}

proc mc_0x1ab_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ab]

    return $rdata
}

proc mc_OUT_OF_RANGE_SOURCE_ID_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ab 0 15 $data 
} 
 
proc mc_OUT_OF_RANGE_SOURCE_ID_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ab 0 15 ] 

    return $rdata 
}

#################################

proc mc_0x1be_print {} {
    puts "addr: 0x1be"
    #fields
    puts "field_name   :BIST_FAIL_ADDR_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1be_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1be $data
}

proc mc_0x1be_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1be]

    return $rdata
}

proc mc_BIST_FAIL_ADDR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1be 0 32 $data 
} 
 
proc mc_BIST_FAIL_ADDR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1be 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1bf_print {} {
    puts "addr: 0x1bf"
    #fields
    puts "field_name   :BIST_FAIL_ADDR_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1bf_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1bf $data
}

proc mc_0x1bf_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1bf]

    return $rdata
}

proc mc_BIST_FAIL_ADDR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1bf 0 7 $data 
} 
 
proc mc_BIST_FAIL_ADDR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1bf 0 7 ] 

    return $rdata 
}

#################################

proc mc_0x1c0_print {} {
    puts "addr: 0x1c0"
    #fields
    puts "field_name   :PORT_CMD_ERROR_ADDR_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1c0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c0 $data
}

proc mc_0x1c0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c0]

    return $rdata
}

proc mc_PORT_CMD_ERROR_ADDR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c0 0 32 $data 
} 
 
proc mc_PORT_CMD_ERROR_ADDR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c0 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1c1_print {} {
    puts "addr: 0x1c1"
    #fields
    puts "field_name   :PORT_CMD_ERROR_ADDR_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :PORT_CMD_ERROR_ID "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :15 "
    puts "default field_value  :0x0 "
    puts "field_name   :PORT_CMD_ERROR_TYPE "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1c1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c1 $data
}

proc mc_0x1c1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c1]

    return $rdata
}

proc mc_PORT_CMD_ERROR_ADDR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c1 0 7 $data 
} 
 
proc mc_PORT_CMD_ERROR_ADDR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c1 0 7 ] 

    return $rdata 
}

proc mc_PORT_CMD_ERROR_ID_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c1 8 15 $data 
} 
 
proc mc_PORT_CMD_ERROR_ID_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c1 8 15 ] 

    return $rdata 
}

proc mc_PORT_CMD_ERROR_TYPE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c1 24 3 $data 
} 
 
proc mc_PORT_CMD_ERROR_TYPE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c1 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x1c2_print {} {
    puts "addr: 0x1c2"
    #fields
    puts "field_name   :PD_NT_ODT_EN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :PD_NT_ODT_EN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :TODTL_2CMD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :TODTH_WR_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
} 

proc mc_0x1c2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c2 $data
}

proc mc_0x1c2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c2]

    return $rdata
}

proc mc_PD_NT_ODT_EN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c2 0 1 $data 
} 
 
proc mc_PD_NT_ODT_EN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c2 0 1 ] 

    return $rdata 
}

proc mc_PD_NT_ODT_EN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c2 8 1 $data 
} 
 
proc mc_PD_NT_ODT_EN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c2 8 1 ] 

    return $rdata 
}

proc mc_TODTL_2CMD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c2 16 8 $data 
} 
 
proc mc_TODTL_2CMD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c2 16 8 ] 

    return $rdata 
}

proc mc_TODTH_WR_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c2 24 4 $data 
} 
 
proc mc_TODTH_WR_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c2 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x1c3_print {} {
    puts "addr: 0x1c3"
    #fields
    puts "field_name   :TODTH_RD_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :TODTL_2CMD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :TODTH_WR_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :TODTH_RD_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1c3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c3 $data
}

proc mc_0x1c3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c3]

    return $rdata
}

proc mc_TODTH_RD_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c3 0 4 $data 
} 
 
proc mc_TODTH_RD_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c3 0 4 ] 

    return $rdata 
}

proc mc_TODTL_2CMD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c3 8 8 $data 
} 
 
proc mc_TODTL_2CMD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c3 8 8 ] 

    return $rdata 
}

proc mc_TODTH_WR_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c3 16 4 $data 
} 
 
proc mc_TODTH_WR_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c3 16 4 ] 

    return $rdata 
}

proc mc_TODTH_RD_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c3 24 4 $data 
} 
 
proc mc_TODTH_RD_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c3 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x1c4_print {} {
    puts "addr: 0x1c4"
    #fields
    puts "field_name   :ODT_EN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :ODT_EN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :7 "
    puts "default field_value  :0x2c "
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :7 "
    puts "default field_value  :0x2c "
} 

proc mc_0x1c4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c4 $data
}

proc mc_0x1c4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c4]

    return $rdata
}

proc mc_ODT_EN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c4 0 1 $data 
} 
 
proc mc_ODT_EN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c4 0 1 ] 

    return $rdata 
}

proc mc_ODT_EN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c4 8 1 $data 
} 
 
proc mc_ODT_EN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c4 8 1 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c4 16 7 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c4 16 7 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c4 24 7 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c4 24 7 ] 

    return $rdata 
}

#################################

proc mc_0x1c5_print {} {
    puts "addr: 0x1c5"
    #fields
    puts "field_name   :ODT_RD_MAP_CS0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x1 "
    puts "field_name   :ODT_WR_MAP_CS0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x1 "
    puts "field_name   :ODT_RD_MAP_CS1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x2 "
    puts "field_name   :ODT_WR_MAP_CS1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x2 "
} 

proc mc_0x1c5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c5 $data
}

proc mc_0x1c5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c5]

    return $rdata
}

proc mc_ODT_RD_MAP_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c5 0 2 $data 
} 
 
proc mc_ODT_RD_MAP_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c5 0 2 ] 

    return $rdata 
}

proc mc_ODT_WR_MAP_CS0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c5 8 2 $data 
} 
 
proc mc_ODT_WR_MAP_CS0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c5 8 2 ] 

    return $rdata 
}

proc mc_ODT_RD_MAP_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c5 16 2 $data 
} 
 
proc mc_ODT_RD_MAP_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c5 16 2 ] 

    return $rdata 
}

proc mc_ODT_WR_MAP_CS1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c5 24 2 $data 
} 
 
proc mc_ODT_WR_MAP_CS1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c5 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x1c6_print {} {
    puts "addr: 0x1c6"
    #fields
    puts "field_name   :RD_TO_ODTH_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x2e "
    puts "field_name   :RD_TO_ODTH_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :7 "
    puts "default field_value  :0x2e "
    puts "field_name   :RW2MRW_DLY_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x16 "
    puts "field_name   :RW2MRW_DLY_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x16 "
} 

proc mc_0x1c6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c6 $data
}

proc mc_0x1c6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c6]

    return $rdata
}

proc mc_RD_TO_ODTH_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c6 0 7 $data 
} 
 
proc mc_RD_TO_ODTH_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c6 0 7 ] 

    return $rdata 
}

proc mc_RD_TO_ODTH_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c6 8 7 $data 
} 
 
proc mc_RD_TO_ODTH_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c6 8 7 ] 

    return $rdata 
}

proc mc_RW2MRW_DLY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c6 16 5 $data 
} 
 
proc mc_RW2MRW_DLY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c6 16 5 ] 

    return $rdata 
}

proc mc_RW2MRW_DLY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c6 24 5 $data 
} 
 
proc mc_RW2MRW_DLY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c6 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x1c7_print {} {
    puts "addr: 0x1c7"
    #fields
    puts "field_name   :R2R_DIFFCS_DLY_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :5 "
    puts "default field_value  :0x3 "
    puts "field_name   :R2W_DIFFCS_DLY_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x4 "
    puts "field_name   :W2R_DIFFCS_DLY_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x3 "
    puts "field_name   :W2W_DIFFCS_DLY_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x6 "
} 

proc mc_0x1c7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c7 $data
}

proc mc_0x1c7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c7]

    return $rdata
}

proc mc_R2R_DIFFCS_DLY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c7 0 5 $data 
} 
 
proc mc_R2R_DIFFCS_DLY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c7 0 5 ] 

    return $rdata 
}

proc mc_R2W_DIFFCS_DLY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c7 8 5 $data 
} 
 
proc mc_R2W_DIFFCS_DLY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c7 8 5 ] 

    return $rdata 
}

proc mc_W2R_DIFFCS_DLY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c7 16 5 $data 
} 
 
proc mc_W2R_DIFFCS_DLY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c7 16 5 ] 

    return $rdata 
}

proc mc_W2W_DIFFCS_DLY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c7 24 5 $data 
} 
 
proc mc_W2W_DIFFCS_DLY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c7 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x1c8_print {} {
    puts "addr: 0x1c8"
    #fields
    puts "field_name   :R2R_DIFFCS_DLY_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :5 "
    puts "default field_value  :0x3 "
    puts "field_name   :R2W_DIFFCS_DLY_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x4 "
    puts "field_name   :W2R_DIFFCS_DLY_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x3 "
    puts "field_name   :W2W_DIFFCS_DLY_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x6 "
} 

proc mc_0x1c8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c8 $data
}

proc mc_0x1c8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c8]

    return $rdata
}

proc mc_R2R_DIFFCS_DLY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c8 0 5 $data 
} 
 
proc mc_R2R_DIFFCS_DLY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c8 0 5 ] 

    return $rdata 
}

proc mc_R2W_DIFFCS_DLY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c8 8 5 $data 
} 
 
proc mc_R2W_DIFFCS_DLY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c8 8 5 ] 

    return $rdata 
}

proc mc_W2R_DIFFCS_DLY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c8 16 5 $data 
} 
 
proc mc_W2R_DIFFCS_DLY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c8 16 5 ] 

    return $rdata 
}

proc mc_W2W_DIFFCS_DLY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c8 24 5 $data 
} 
 
proc mc_W2W_DIFFCS_DLY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c8 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x1c9_print {} {
    puts "addr: 0x1c9"
    #fields
    puts "field_name   :R2W_SAMECS_DLY_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :5 "
    puts "default field_value  :0x7 "
    puts "field_name   :R2W_SAMECS_DLY_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :5 "
    puts "default field_value  :0x7 "
    puts "field_name   :R2R_SAMECS_DLY "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
    puts "field_name   :W2R_SAMECS_DLY "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1c9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1c9 $data
}

proc mc_0x1c9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1c9]

    return $rdata
}

proc mc_R2W_SAMECS_DLY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c9 0 5 $data 
} 
 
proc mc_R2W_SAMECS_DLY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c9 0 5 ] 

    return $rdata 
}

proc mc_R2W_SAMECS_DLY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c9 8 5 $data 
} 
 
proc mc_R2W_SAMECS_DLY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c9 8 5 ] 

    return $rdata 
}

proc mc_R2R_SAMECS_DLY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c9 16 5 $data 
} 
 
proc mc_R2R_SAMECS_DLY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c9 16 5 ] 

    return $rdata 
}

proc mc_W2R_SAMECS_DLY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1c9 24 5 $data 
} 
 
proc mc_W2R_SAMECS_DLY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1c9 24 5 ] 

    return $rdata 
}

#################################

proc mc_0x1ca_print {} {
    puts "addr: 0x1ca"
    #fields
    puts "field_name   :W2W_SAMECS_DLY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :5 "
    puts "default field_value  :0x0 "
    puts "field_name   :TDQSCK_MAX_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
    puts "field_name   :TDQSCK_MIN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
    puts "field_name   :TDQSCK_MAX_F1 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1ca_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ca $data
}

proc mc_0x1ca_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ca]

    return $rdata
}

proc mc_W2W_SAMECS_DLY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ca 0 5 $data 
} 
 
proc mc_W2W_SAMECS_DLY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ca 0 5 ] 

    return $rdata 
}

proc mc_TDQSCK_MAX_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ca 8 3 $data 
} 
 
proc mc_TDQSCK_MAX_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ca 8 3 ] 

    return $rdata 
}

proc mc_TDQSCK_MIN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ca 16 3 $data 
} 
 
proc mc_TDQSCK_MIN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ca 16 3 ] 

    return $rdata 
}

proc mc_TDQSCK_MAX_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ca 24 3 $data 
} 
 
proc mc_TDQSCK_MAX_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ca 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x1cb_print {} {
    puts "addr: 0x1cb"
    #fields
    puts "field_name   :TDQSCK_MIN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_ALL_STROBES_USED_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_FIXED_PORT_PRIORITY_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_R_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x4 "
} 

proc mc_0x1cb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1cb $data
}

proc mc_0x1cb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1cb]

    return $rdata
}

proc mc_TDQSCK_MIN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cb 0 3 $data 
} 
 
proc mc_TDQSCK_MIN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cb 0 3 ] 

    return $rdata 
}

proc mc_AXI0_ALL_STROBES_USED_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cb 8 1 $data 
} 
 
proc mc_AXI0_ALL_STROBES_USED_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cb 8 1 ] 

    return $rdata 
}

proc mc_AXI0_FIXED_PORT_PRIORITY_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cb 16 1 $data 
} 
 
proc mc_AXI0_FIXED_PORT_PRIORITY_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cb 16 1 ] 

    return $rdata 
}

proc mc_AXI0_R_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cb 24 3 $data 
} 
 
proc mc_AXI0_R_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cb 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x1cc_print {} {
    puts "addr: 0x1cc"
    #fields
    puts "field_name   :AXI0_W_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x4 "
    puts "field_name   :AXI1_ALL_STROBES_USED_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI1_FIXED_PORT_PRIORITY_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI1_R_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x4 "
} 

proc mc_0x1cc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1cc $data
}

proc mc_0x1cc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1cc]

    return $rdata
}

proc mc_AXI0_W_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cc 0 3 $data 
} 
 
proc mc_AXI0_W_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cc 0 3 ] 

    return $rdata 
}

proc mc_AXI1_ALL_STROBES_USED_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cc 8 1 $data 
} 
 
proc mc_AXI1_ALL_STROBES_USED_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cc 8 1 ] 

    return $rdata 
}

proc mc_AXI1_FIXED_PORT_PRIORITY_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cc 16 1 $data 
} 
 
proc mc_AXI1_FIXED_PORT_PRIORITY_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cc 16 1 ] 

    return $rdata 
}

proc mc_AXI1_R_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cc 24 3 $data 
} 
 
proc mc_AXI1_R_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cc 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x1cd_print {} {
    puts "addr: 0x1cd"
    #fields
    puts "field_name   :AXI1_W_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x4 "
} 

proc mc_0x1cd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1cd $data
}

proc mc_0x1cd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1cd]

    return $rdata
}

proc mc_AXI1_W_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1cd 0 3 $data 
} 
 
proc mc_AXI1_W_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1cd 0 3 ] 

    return $rdata 
}

#################################

proc mc_0x1d0_print {} {
    puts "addr: 0x1d0"
    #fields
    puts "field_name   :PARITY_ERROR_ADDRESS_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1d0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1d0 $data
}

proc mc_0x1d0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1d0]

    return $rdata
}

proc mc_PARITY_ERROR_ADDRESS_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1d0 0 32 $data 
} 
 
proc mc_PARITY_ERROR_ADDRESS_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1d0 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x1d1_print {} {
    puts "addr: 0x1d1"
    #fields
    puts "field_name   :PARITY_ERROR_ADDRESS_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
    puts "field_name   :PARITY_ERROR_MASTER_ID "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :15 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1d1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1d1 $data
}

proc mc_0x1d1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1d1]

    return $rdata
}

proc mc_PARITY_ERROR_ADDRESS_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1d1 0 7 $data 
} 
 
proc mc_PARITY_ERROR_ADDRESS_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1d1 0 7 ] 

    return $rdata 
}

proc mc_PARITY_ERROR_MASTER_ID_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1d1 8 15 $data 
} 
 
proc mc_PARITY_ERROR_MASTER_ID_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1d1 8 15 ] 

    return $rdata 
}

#################################

proc mc_0x1d2_print {} {
    puts "addr: 0x1d2"
    #fields
    puts "field_name   :PARITY_ERROR_BUS_CHANNEL "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :13 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1d2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1d2 $data
}

proc mc_0x1d2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1d2]

    return $rdata
}

proc mc_PARITY_ERROR_BUS_CHANNEL_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1d2 0 13 $data 
} 
 
proc mc_PARITY_ERROR_BUS_CHANNEL_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1d2 0 13 ] 

    return $rdata 
}

#################################

proc mc_0x1dc_print {} {
    puts "addr: 0x1dc"
    #fields
    puts "field_name   :PORT_ADDR_PROTECTION_EN "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI0_ADDRESS_RANGE_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1dc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1dc $data
}

proc mc_0x1dc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1dc]

    return $rdata
}

proc mc_PORT_ADDR_PROTECTION_EN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1dc 0 1 $data 
} 
 
proc mc_PORT_ADDR_PROTECTION_EN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1dc 0 1 ] 

    return $rdata 
}

proc mc_AXI0_ADDRESS_RANGE_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1dc 8 1 $data 
} 
 
proc mc_AXI0_ADDRESS_RANGE_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1dc 8 1 ] 

    return $rdata 
}

#################################

proc mc_0x1dd_print {} {
    puts "addr: 0x1dd"
    #fields
    puts "field_name   :AXI0_START_ADDR_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1dd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1dd $data
}

proc mc_0x1dd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1dd]

    return $rdata
}

proc mc_AXI0_START_ADDR_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1dd 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1dd 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1de_print {} {
    puts "addr: 0x1de"
    #fields
    puts "field_name   :AXI0_END_ADDR_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x1de_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1de $data
}

proc mc_0x1de_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1de]

    return $rdata
}

proc mc_AXI0_END_ADDR_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1de 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1de 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1df_print {} {
    puts "addr: 0x1df"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x1df_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1df $data
}

proc mc_0x1df_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1df]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1df 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1df 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1df 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1df 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x1e0_print {} {
    puts "addr: 0x1e0"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1e0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e0 $data
}

proc mc_0x1e0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e0]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e0 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e0 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e0 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e0 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x1e1_print {} {
    puts "addr: 0x1e1"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1e1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e1 $data
}

proc mc_0x1e1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e1]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e1 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e1 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x1e2_print {} {
    puts "addr: 0x1e2"
    #fields
    puts "field_name   :AXI0_START_ADDR_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1e2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e2 $data
}

proc mc_0x1e2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e2]

    return $rdata
}

proc mc_AXI0_START_ADDR_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e2 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e2 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1e3_print {} {
    puts "addr: 0x1e3"
    #fields
    puts "field_name   :AXI0_END_ADDR_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x1e3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e3 $data
}

proc mc_0x1e3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e3]

    return $rdata
}

proc mc_AXI0_END_ADDR_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e3 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e3 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1e4_print {} {
    puts "addr: 0x1e4"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x1e4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e4 $data
}

proc mc_0x1e4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e4]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e4 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e4 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e4 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e4 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x1e5_print {} {
    puts "addr: 0x1e5"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1e5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e5 $data
}

proc mc_0x1e5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e5]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e5 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e5 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e5 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e5 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x1e6_print {} {
    puts "addr: 0x1e6"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1e6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e6 $data
}

proc mc_0x1e6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e6]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e6 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e6 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x1e7_print {} {
    puts "addr: 0x1e7"
    #fields
    puts "field_name   :AXI0_START_ADDR_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1e7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e7 $data
}

proc mc_0x1e7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e7]

    return $rdata
}

proc mc_AXI0_START_ADDR_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e7 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e7 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1e8_print {} {
    puts "addr: 0x1e8"
    #fields
    puts "field_name   :AXI0_END_ADDR_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x1e8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e8 $data
}

proc mc_0x1e8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e8]

    return $rdata
}

proc mc_AXI0_END_ADDR_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e8 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e8 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1e9_print {} {
    puts "addr: 0x1e9"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_2 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x1e9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1e9 $data
}

proc mc_0x1e9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1e9]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e9 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e9 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1e9 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1e9 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x1ea_print {} {
    puts "addr: 0x1ea"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_2 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1ea_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ea $data
}

proc mc_0x1ea_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ea]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ea 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ea 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ea 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ea 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x1eb_print {} {
    puts "addr: 0x1eb"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1eb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1eb $data
}

proc mc_0x1eb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1eb]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1eb 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1eb 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x1ec_print {} {
    puts "addr: 0x1ec"
    #fields
    puts "field_name   :AXI0_START_ADDR_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1ec_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ec $data
}

proc mc_0x1ec_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ec]

    return $rdata
}

proc mc_AXI0_START_ADDR_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ec 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ec 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1ed_print {} {
    puts "addr: 0x1ed"
    #fields
    puts "field_name   :AXI0_END_ADDR_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x1ed_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ed $data
}

proc mc_0x1ed_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ed]

    return $rdata
}

proc mc_AXI0_END_ADDR_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ed 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ed 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1ee_print {} {
    puts "addr: 0x1ee"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_3 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x1ee_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ee $data
}

proc mc_0x1ee_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ee]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ee 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ee 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ee 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ee 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x1ef_print {} {
    puts "addr: 0x1ef"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_3 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1ef_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ef $data
}

proc mc_0x1ef_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ef]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ef 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ef 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ef 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ef 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x1f0_print {} {
    puts "addr: 0x1f0"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1f0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f0 $data
}

proc mc_0x1f0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f0]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f0 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f0 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x1f1_print {} {
    puts "addr: 0x1f1"
    #fields
    puts "field_name   :AXI0_START_ADDR_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1f1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f1 $data
}

proc mc_0x1f1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f1]

    return $rdata
}

proc mc_AXI0_START_ADDR_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f1 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f1 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1f2_print {} {
    puts "addr: 0x1f2"
    #fields
    puts "field_name   :AXI0_END_ADDR_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x1f2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f2 $data
}

proc mc_0x1f2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f2]

    return $rdata
}

proc mc_AXI0_END_ADDR_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f2 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f2 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1f3_print {} {
    puts "addr: 0x1f3"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_4 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x1f3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f3 $data
}

proc mc_0x1f3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f3]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f3 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f3 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f3 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f3 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x1f4_print {} {
    puts "addr: 0x1f4"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_4 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1f4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f4 $data
}

proc mc_0x1f4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f4]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f4 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f4 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f4 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f4 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x1f5_print {} {
    puts "addr: 0x1f5"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1f5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f5 $data
}

proc mc_0x1f5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f5]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f5 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f5 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x1f6_print {} {
    puts "addr: 0x1f6"
    #fields
    puts "field_name   :AXI0_START_ADDR_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1f6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f6 $data
}

proc mc_0x1f6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f6]

    return $rdata
}

proc mc_AXI0_START_ADDR_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f6 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f6 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1f7_print {} {
    puts "addr: 0x1f7"
    #fields
    puts "field_name   :AXI0_END_ADDR_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x1f7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f7 $data
}

proc mc_0x1f7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f7]

    return $rdata
}

proc mc_AXI0_END_ADDR_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f7 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f7 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1f8_print {} {
    puts "addr: 0x1f8"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_5 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x1f8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f8 $data
}

proc mc_0x1f8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f8]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f8 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f8 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f8 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f8 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x1f9_print {} {
    puts "addr: 0x1f9"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_5 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1f9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1f9 $data
}

proc mc_0x1f9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1f9]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f9 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f9 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1f9 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1f9 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x1fa_print {} {
    puts "addr: 0x1fa"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1fa_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1fa $data
}

proc mc_0x1fa_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1fa]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1fa 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1fa 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x1fb_print {} {
    puts "addr: 0x1fb"
    #fields
    puts "field_name   :AXI0_START_ADDR_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x1fb_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1fb $data
}

proc mc_0x1fb_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1fb]

    return $rdata
}

proc mc_AXI0_START_ADDR_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1fb 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1fb 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1fc_print {} {
    puts "addr: 0x1fc"
    #fields
    puts "field_name   :AXI0_END_ADDR_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x1fc_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1fc $data
}

proc mc_0x1fc_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1fc]

    return $rdata
}

proc mc_AXI0_END_ADDR_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1fc 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1fc 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x1fd_print {} {
    puts "addr: 0x1fd"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_6 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x1fd_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1fd $data
}

proc mc_0x1fd_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1fd]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1fd 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1fd 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1fd 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1fd 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x1fe_print {} {
    puts "addr: 0x1fe"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_6 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1fe_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1fe $data
}

proc mc_0x1fe_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1fe]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1fe 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1fe 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1fe 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1fe 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x1ff_print {} {
    puts "addr: 0x1ff"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x1ff_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x1ff $data
}

proc mc_0x1ff_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x1ff]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x1ff 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x1ff 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x200_print {} {
    puts "addr: 0x200"
    #fields
    puts "field_name   :AXI0_START_ADDR_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x200_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x200 $data
}

proc mc_0x200_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x200]

    return $rdata
}

proc mc_AXI0_START_ADDR_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x200 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x200 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x201_print {} {
    puts "addr: 0x201"
    #fields
    puts "field_name   :AXI0_END_ADDR_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x201_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x201 $data
}

proc mc_0x201_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x201]

    return $rdata
}

proc mc_AXI0_END_ADDR_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x201 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x201 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x202_print {} {
    puts "addr: 0x202"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_7 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x202_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x202 $data
}

proc mc_0x202_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x202]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x202 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x202 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x202 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x202 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x203_print {} {
    puts "addr: 0x203"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_7 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x203_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x203 $data
}

proc mc_0x203_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x203]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x203 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x203 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x203 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x203 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x204_print {} {
    puts "addr: 0x204"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x204_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x204 $data
}

proc mc_0x204_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x204]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x204 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x204 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x205_print {} {
    puts "addr: 0x205"
    #fields
    puts "field_name   :AXI0_START_ADDR_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x205_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x205 $data
}

proc mc_0x205_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x205]

    return $rdata
}

proc mc_AXI0_START_ADDR_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x205 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x205 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x206_print {} {
    puts "addr: 0x206"
    #fields
    puts "field_name   :AXI0_END_ADDR_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x206_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x206 $data
}

proc mc_0x206_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x206]

    return $rdata
}

proc mc_AXI0_END_ADDR_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x206 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x206 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x207_print {} {
    puts "addr: 0x207"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_8 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x207_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x207 $data
}

proc mc_0x207_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x207]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x207 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x207 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x207 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x207 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x208_print {} {
    puts "addr: 0x208"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_8 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x208_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x208 $data
}

proc mc_0x208_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x208]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x208 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x208 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x208 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x208 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x209_print {} {
    puts "addr: 0x209"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x209_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x209 $data
}

proc mc_0x209_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x209]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x209 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x209 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x20a_print {} {
    puts "addr: 0x20a"
    #fields
    puts "field_name   :AXI0_START_ADDR_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x20a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x20a $data
}

proc mc_0x20a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x20a]

    return $rdata
}

proc mc_AXI0_START_ADDR_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20a 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20a 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x20b_print {} {
    puts "addr: 0x20b"
    #fields
    puts "field_name   :AXI0_END_ADDR_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x20b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x20b $data
}

proc mc_0x20b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x20b]

    return $rdata
}

proc mc_AXI0_END_ADDR_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20b 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20b 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x20c_print {} {
    puts "addr: 0x20c"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_9 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x20c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x20c $data
}

proc mc_0x20c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x20c]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20c 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20c 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20c 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20c 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x20d_print {} {
    puts "addr: 0x20d"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_9 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x20d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x20d $data
}

proc mc_0x20d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x20d]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20d 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20d 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20d 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20d 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x20e_print {} {
    puts "addr: 0x20e"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x20e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x20e $data
}

proc mc_0x20e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x20e]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20e 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20e 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x20f_print {} {
    puts "addr: 0x20f"
    #fields
    puts "field_name   :AXI0_START_ADDR_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x20f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x20f $data
}

proc mc_0x20f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x20f]

    return $rdata
}

proc mc_AXI0_START_ADDR_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x20f 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x20f 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x210_print {} {
    puts "addr: 0x210"
    #fields
    puts "field_name   :AXI0_END_ADDR_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x210_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x210 $data
}

proc mc_0x210_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x210]

    return $rdata
}

proc mc_AXI0_END_ADDR_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x210 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x210 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x211_print {} {
    puts "addr: 0x211"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_10 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x211_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x211 $data
}

proc mc_0x211_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x211]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x211 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x211 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x211 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x211 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x212_print {} {
    puts "addr: 0x212"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_10 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x212_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x212 $data
}

proc mc_0x212_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x212]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x212 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x212 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x212 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x212 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x213_print {} {
    puts "addr: 0x213"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x213_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x213 $data
}

proc mc_0x213_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x213]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x213 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x213 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x214_print {} {
    puts "addr: 0x214"
    #fields
    puts "field_name   :AXI0_START_ADDR_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x214_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x214 $data
}

proc mc_0x214_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x214]

    return $rdata
}

proc mc_AXI0_START_ADDR_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x214 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x214 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x215_print {} {
    puts "addr: 0x215"
    #fields
    puts "field_name   :AXI0_END_ADDR_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x215_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x215 $data
}

proc mc_0x215_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x215]

    return $rdata
}

proc mc_AXI0_END_ADDR_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x215 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x215 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x216_print {} {
    puts "addr: 0x216"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_11 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x216_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x216 $data
}

proc mc_0x216_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x216]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x216 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x216 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x216 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x216 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x217_print {} {
    puts "addr: 0x217"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_11 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x217_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x217 $data
}

proc mc_0x217_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x217]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x217 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x217 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x217 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x217 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x218_print {} {
    puts "addr: 0x218"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x218_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x218 $data
}

proc mc_0x218_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x218]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x218 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x218 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x219_print {} {
    puts "addr: 0x219"
    #fields
    puts "field_name   :AXI0_START_ADDR_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x219_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x219 $data
}

proc mc_0x219_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x219]

    return $rdata
}

proc mc_AXI0_START_ADDR_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x219 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x219 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x21a_print {} {
    puts "addr: 0x21a"
    #fields
    puts "field_name   :AXI0_END_ADDR_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x21a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x21a $data
}

proc mc_0x21a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x21a]

    return $rdata
}

proc mc_AXI0_END_ADDR_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21a 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21a 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x21b_print {} {
    puts "addr: 0x21b"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_12 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x21b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x21b $data
}

proc mc_0x21b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x21b]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21b 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21b 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21b 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21b 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x21c_print {} {
    puts "addr: 0x21c"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_12 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x21c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x21c $data
}

proc mc_0x21c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x21c]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21c 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21c 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21c 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21c 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x21d_print {} {
    puts "addr: 0x21d"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x21d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x21d $data
}

proc mc_0x21d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x21d]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21d 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21d 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x21e_print {} {
    puts "addr: 0x21e"
    #fields
    puts "field_name   :AXI0_START_ADDR_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x21e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x21e $data
}

proc mc_0x21e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x21e]

    return $rdata
}

proc mc_AXI0_START_ADDR_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21e 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21e 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x21f_print {} {
    puts "addr: 0x21f"
    #fields
    puts "field_name   :AXI0_END_ADDR_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x21f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x21f $data
}

proc mc_0x21f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x21f]

    return $rdata
}

proc mc_AXI0_END_ADDR_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x21f 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x21f 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x220_print {} {
    puts "addr: 0x220"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_13 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x220_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x220 $data
}

proc mc_0x220_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x220]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x220 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x220 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x220 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x220 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x221_print {} {
    puts "addr: 0x221"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_13 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x221_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x221 $data
}

proc mc_0x221_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x221]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x221 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x221 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x221 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x221 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x222_print {} {
    puts "addr: 0x222"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x222_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x222 $data
}

proc mc_0x222_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x222]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x222 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x222 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x223_print {} {
    puts "addr: 0x223"
    #fields
    puts "field_name   :AXI0_START_ADDR_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x223_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x223 $data
}

proc mc_0x223_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x223]

    return $rdata
}

proc mc_AXI0_START_ADDR_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x223 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x223 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x224_print {} {
    puts "addr: 0x224"
    #fields
    puts "field_name   :AXI0_END_ADDR_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x224_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x224 $data
}

proc mc_0x224_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x224]

    return $rdata
}

proc mc_AXI0_END_ADDR_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x224 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x224 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x225_print {} {
    puts "addr: 0x225"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_14 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x225_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x225 $data
}

proc mc_0x225_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x225]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x225 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x225 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x225 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x225 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x226_print {} {
    puts "addr: 0x226"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_14 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x226_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x226 $data
}

proc mc_0x226_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x226]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x226 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x226 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x226 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x226 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x227_print {} {
    puts "addr: 0x227"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x227_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x227 $data
}

proc mc_0x227_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x227]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x227 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x227 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x228_print {} {
    puts "addr: 0x228"
    #fields
    puts "field_name   :AXI0_START_ADDR_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x228_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x228 $data
}

proc mc_0x228_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x228]

    return $rdata
}

proc mc_AXI0_START_ADDR_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x228 0 25 $data 
} 
 
proc mc_AXI0_START_ADDR_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x228 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x229_print {} {
    puts "addr: 0x229"
    #fields
    puts "field_name   :AXI0_END_ADDR_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x229_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x229 $data
}

proc mc_0x229_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x229]

    return $rdata
}

proc mc_AXI0_END_ADDR_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x229 0 25 $data 
} 
 
proc mc_AXI0_END_ADDR_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x229 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x22a_print {} {
    puts "addr: 0x22a"
    #fields
    puts "field_name   :AXI0_RANGE_PROT_BITS_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_15 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x22a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x22a $data
}

proc mc_0x22a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x22a]

    return $rdata
}

proc mc_AXI0_RANGE_PROT_BITS_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22a 0 2 $data 
} 
 
proc mc_AXI0_RANGE_PROT_BITS_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22a 0 2 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22a 8 16 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22a 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x22b_print {} {
    puts "addr: 0x22b"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_15 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x22b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x22b $data
}

proc mc_0x22b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x22b]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22b 0 16 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22b 0 16 ] 

    return $rdata 
}

proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22b 16 14 $data 
} 
 
proc mc_AXI0_RANGE_RID_CHECK_BITS_ID_LOOKUP_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22b 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x22c_print {} {
    puts "addr: 0x22c"
    #fields
    puts "field_name   :AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
    puts "field_name   :AXI1_ADDRESS_RANGE_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x22c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x22c $data
}

proc mc_0x22c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x22c]

    return $rdata
}

proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22c 0 14 $data 
} 
 
proc mc_AXI0_RANGE_WID_CHECK_BITS_ID_LOOKUP_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22c 0 14 ] 

    return $rdata 
}

proc mc_AXI1_ADDRESS_RANGE_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22c 16 1 $data 
} 
 
proc mc_AXI1_ADDRESS_RANGE_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22c 16 1 ] 

    return $rdata 
}

#################################

proc mc_0x22d_print {} {
    puts "addr: 0x22d"
    #fields
    puts "field_name   :AXI1_START_ADDR_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x22d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x22d $data
}

proc mc_0x22d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x22d]

    return $rdata
}

proc mc_AXI1_START_ADDR_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22d 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22d 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x22e_print {} {
    puts "addr: 0x22e"
    #fields
    puts "field_name   :AXI1_END_ADDR_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x22e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x22e $data
}

proc mc_0x22e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x22e]

    return $rdata
}

proc mc_AXI1_END_ADDR_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22e 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22e 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x22f_print {} {
    puts "addr: 0x22f"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x22f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x22f $data
}

proc mc_0x22f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x22f]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22f 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22f 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x22f 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x22f 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x230_print {} {
    puts "addr: 0x230"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x230_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x230 $data
}

proc mc_0x230_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x230]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x230 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x230 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x230 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x230 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x231_print {} {
    puts "addr: 0x231"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x231_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x231 $data
}

proc mc_0x231_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x231]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x231 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x231 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x232_print {} {
    puts "addr: 0x232"
    #fields
    puts "field_name   :AXI1_START_ADDR_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x232_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x232 $data
}

proc mc_0x232_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x232]

    return $rdata
}

proc mc_AXI1_START_ADDR_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x232 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x232 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x233_print {} {
    puts "addr: 0x233"
    #fields
    puts "field_name   :AXI1_END_ADDR_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x233_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x233 $data
}

proc mc_0x233_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x233]

    return $rdata
}

proc mc_AXI1_END_ADDR_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x233 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x233 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x234_print {} {
    puts "addr: 0x234"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x234_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x234 $data
}

proc mc_0x234_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x234]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x234 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x234 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x234 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x234 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x235_print {} {
    puts "addr: 0x235"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x235_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x235 $data
}

proc mc_0x235_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x235]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x235 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x235 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x235 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x235 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x236_print {} {
    puts "addr: 0x236"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x236_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x236 $data
}

proc mc_0x236_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x236]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x236 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x236 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x237_print {} {
    puts "addr: 0x237"
    #fields
    puts "field_name   :AXI1_START_ADDR_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x237_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x237 $data
}

proc mc_0x237_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x237]

    return $rdata
}

proc mc_AXI1_START_ADDR_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x237 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x237 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x238_print {} {
    puts "addr: 0x238"
    #fields
    puts "field_name   :AXI1_END_ADDR_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x238_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x238 $data
}

proc mc_0x238_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x238]

    return $rdata
}

proc mc_AXI1_END_ADDR_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x238 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x238 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x239_print {} {
    puts "addr: 0x239"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_2 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x239_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x239 $data
}

proc mc_0x239_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x239]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x239 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x239 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x239 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x239 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x23a_print {} {
    puts "addr: 0x23a"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_2 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x23a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x23a $data
}

proc mc_0x23a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x23a]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23a 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23a 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23a 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23a 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x23b_print {} {
    puts "addr: 0x23b"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x23b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x23b $data
}

proc mc_0x23b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x23b]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23b 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23b 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x23c_print {} {
    puts "addr: 0x23c"
    #fields
    puts "field_name   :AXI1_START_ADDR_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x23c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x23c $data
}

proc mc_0x23c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x23c]

    return $rdata
}

proc mc_AXI1_START_ADDR_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23c 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23c 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x23d_print {} {
    puts "addr: 0x23d"
    #fields
    puts "field_name   :AXI1_END_ADDR_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x23d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x23d $data
}

proc mc_0x23d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x23d]

    return $rdata
}

proc mc_AXI1_END_ADDR_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23d 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23d 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x23e_print {} {
    puts "addr: 0x23e"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_3 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x23e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x23e $data
}

proc mc_0x23e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x23e]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23e 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23e 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23e 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23e 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x23f_print {} {
    puts "addr: 0x23f"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_3 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x23f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x23f $data
}

proc mc_0x23f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x23f]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23f 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23f 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x23f 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x23f 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x240_print {} {
    puts "addr: 0x240"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x240_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x240 $data
}

proc mc_0x240_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x240]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x240 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x240 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x241_print {} {
    puts "addr: 0x241"
    #fields
    puts "field_name   :AXI1_START_ADDR_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x241_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x241 $data
}

proc mc_0x241_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x241]

    return $rdata
}

proc mc_AXI1_START_ADDR_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x241 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x241 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x242_print {} {
    puts "addr: 0x242"
    #fields
    puts "field_name   :AXI1_END_ADDR_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x242_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x242 $data
}

proc mc_0x242_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x242]

    return $rdata
}

proc mc_AXI1_END_ADDR_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x242 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x242 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x243_print {} {
    puts "addr: 0x243"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_4 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x243_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x243 $data
}

proc mc_0x243_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x243]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x243 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x243 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x243 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x243 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x244_print {} {
    puts "addr: 0x244"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_4 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x244_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x244 $data
}

proc mc_0x244_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x244]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x244 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x244 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x244 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x244 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x245_print {} {
    puts "addr: 0x245"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x245_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x245 $data
}

proc mc_0x245_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x245]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x245 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x245 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x246_print {} {
    puts "addr: 0x246"
    #fields
    puts "field_name   :AXI1_START_ADDR_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x246_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x246 $data
}

proc mc_0x246_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x246]

    return $rdata
}

proc mc_AXI1_START_ADDR_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x246 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x246 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x247_print {} {
    puts "addr: 0x247"
    #fields
    puts "field_name   :AXI1_END_ADDR_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x247_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x247 $data
}

proc mc_0x247_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x247]

    return $rdata
}

proc mc_AXI1_END_ADDR_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x247 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x247 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x248_print {} {
    puts "addr: 0x248"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_5 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x248_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x248 $data
}

proc mc_0x248_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x248]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x248 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x248 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x248 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x248 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x249_print {} {
    puts "addr: 0x249"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_5 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x249_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x249 $data
}

proc mc_0x249_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x249]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x249 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x249 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x249 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x249 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x24a_print {} {
    puts "addr: 0x24a"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x24a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x24a $data
}

proc mc_0x24a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x24a]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24a 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24a 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x24b_print {} {
    puts "addr: 0x24b"
    #fields
    puts "field_name   :AXI1_START_ADDR_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x24b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x24b $data
}

proc mc_0x24b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x24b]

    return $rdata
}

proc mc_AXI1_START_ADDR_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24b 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24b 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x24c_print {} {
    puts "addr: 0x24c"
    #fields
    puts "field_name   :AXI1_END_ADDR_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x24c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x24c $data
}

proc mc_0x24c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x24c]

    return $rdata
}

proc mc_AXI1_END_ADDR_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24c 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24c 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x24d_print {} {
    puts "addr: 0x24d"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_6 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x24d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x24d $data
}

proc mc_0x24d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x24d]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24d 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24d 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24d 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24d 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x24e_print {} {
    puts "addr: 0x24e"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_6 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x24e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x24e $data
}

proc mc_0x24e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x24e]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24e 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24e 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24e 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24e 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x24f_print {} {
    puts "addr: 0x24f"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x24f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x24f $data
}

proc mc_0x24f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x24f]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x24f 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x24f 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x250_print {} {
    puts "addr: 0x250"
    #fields
    puts "field_name   :AXI1_START_ADDR_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x250_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x250 $data
}

proc mc_0x250_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x250]

    return $rdata
}

proc mc_AXI1_START_ADDR_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x250 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x250 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x251_print {} {
    puts "addr: 0x251"
    #fields
    puts "field_name   :AXI1_END_ADDR_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x251_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x251 $data
}

proc mc_0x251_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x251]

    return $rdata
}

proc mc_AXI1_END_ADDR_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x251 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x251 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x252_print {} {
    puts "addr: 0x252"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_7 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x252_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x252 $data
}

proc mc_0x252_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x252]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x252 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x252 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x252 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x252 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x253_print {} {
    puts "addr: 0x253"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_7 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x253_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x253 $data
}

proc mc_0x253_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x253]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x253 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x253 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x253 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x253 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x254_print {} {
    puts "addr: 0x254"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x254_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x254 $data
}

proc mc_0x254_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x254]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x254 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x254 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x255_print {} {
    puts "addr: 0x255"
    #fields
    puts "field_name   :AXI1_START_ADDR_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x255_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x255 $data
}

proc mc_0x255_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x255]

    return $rdata
}

proc mc_AXI1_START_ADDR_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x255 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x255 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x256_print {} {
    puts "addr: 0x256"
    #fields
    puts "field_name   :AXI1_END_ADDR_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x256_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x256 $data
}

proc mc_0x256_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x256]

    return $rdata
}

proc mc_AXI1_END_ADDR_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x256 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x256 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x257_print {} {
    puts "addr: 0x257"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_8 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x257_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x257 $data
}

proc mc_0x257_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x257]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x257 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x257 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x257 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x257 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x258_print {} {
    puts "addr: 0x258"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_8 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x258_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x258 $data
}

proc mc_0x258_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x258]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x258 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x258 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x258 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x258 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x259_print {} {
    puts "addr: 0x259"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x259_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x259 $data
}

proc mc_0x259_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x259]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x259 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x259 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x25a_print {} {
    puts "addr: 0x25a"
    #fields
    puts "field_name   :AXI1_START_ADDR_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x25a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x25a $data
}

proc mc_0x25a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x25a]

    return $rdata
}

proc mc_AXI1_START_ADDR_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25a 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25a 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x25b_print {} {
    puts "addr: 0x25b"
    #fields
    puts "field_name   :AXI1_END_ADDR_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x25b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x25b $data
}

proc mc_0x25b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x25b]

    return $rdata
}

proc mc_AXI1_END_ADDR_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25b 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25b 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x25c_print {} {
    puts "addr: 0x25c"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_9 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x25c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x25c $data
}

proc mc_0x25c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x25c]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25c 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25c 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25c 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25c 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x25d_print {} {
    puts "addr: 0x25d"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_9 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x25d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x25d $data
}

proc mc_0x25d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x25d]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25d 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25d 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25d 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25d 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x25e_print {} {
    puts "addr: 0x25e"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x25e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x25e $data
}

proc mc_0x25e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x25e]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25e 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25e 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x25f_print {} {
    puts "addr: 0x25f"
    #fields
    puts "field_name   :AXI1_START_ADDR_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x25f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x25f $data
}

proc mc_0x25f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x25f]

    return $rdata
}

proc mc_AXI1_START_ADDR_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x25f 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x25f 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x260_print {} {
    puts "addr: 0x260"
    #fields
    puts "field_name   :AXI1_END_ADDR_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x260_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x260 $data
}

proc mc_0x260_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x260]

    return $rdata
}

proc mc_AXI1_END_ADDR_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x260 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x260 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x261_print {} {
    puts "addr: 0x261"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_10 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x261_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x261 $data
}

proc mc_0x261_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x261]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x261 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x261 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x261 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x261 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x262_print {} {
    puts "addr: 0x262"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_10 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x262_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x262 $data
}

proc mc_0x262_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x262]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x262 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x262 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x262 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x262 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x263_print {} {
    puts "addr: 0x263"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x263_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x263 $data
}

proc mc_0x263_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x263]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x263 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x263 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x264_print {} {
    puts "addr: 0x264"
    #fields
    puts "field_name   :AXI1_START_ADDR_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x264_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x264 $data
}

proc mc_0x264_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x264]

    return $rdata
}

proc mc_AXI1_START_ADDR_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x264 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x264 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x265_print {} {
    puts "addr: 0x265"
    #fields
    puts "field_name   :AXI1_END_ADDR_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x265_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x265 $data
}

proc mc_0x265_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x265]

    return $rdata
}

proc mc_AXI1_END_ADDR_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x265 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x265 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x266_print {} {
    puts "addr: 0x266"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_11 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x266_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x266 $data
}

proc mc_0x266_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x266]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x266 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x266 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x266 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x266 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x267_print {} {
    puts "addr: 0x267"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_11 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x267_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x267 $data
}

proc mc_0x267_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x267]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x267 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x267 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x267 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x267 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x268_print {} {
    puts "addr: 0x268"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x268_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x268 $data
}

proc mc_0x268_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x268]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x268 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x268 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x269_print {} {
    puts "addr: 0x269"
    #fields
    puts "field_name   :AXI1_START_ADDR_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x269_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x269 $data
}

proc mc_0x269_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x269]

    return $rdata
}

proc mc_AXI1_START_ADDR_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x269 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x269 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x26a_print {} {
    puts "addr: 0x26a"
    #fields
    puts "field_name   :AXI1_END_ADDR_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x26a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x26a $data
}

proc mc_0x26a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x26a]

    return $rdata
}

proc mc_AXI1_END_ADDR_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26a 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26a 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x26b_print {} {
    puts "addr: 0x26b"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_12 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x26b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x26b $data
}

proc mc_0x26b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x26b]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26b 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26b 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26b 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26b 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x26c_print {} {
    puts "addr: 0x26c"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_12 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x26c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x26c $data
}

proc mc_0x26c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x26c]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26c 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26c 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26c 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26c 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x26d_print {} {
    puts "addr: 0x26d"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x26d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x26d $data
}

proc mc_0x26d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x26d]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26d 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26d 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x26e_print {} {
    puts "addr: 0x26e"
    #fields
    puts "field_name   :AXI1_START_ADDR_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x26e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x26e $data
}

proc mc_0x26e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x26e]

    return $rdata
}

proc mc_AXI1_START_ADDR_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26e 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26e 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x26f_print {} {
    puts "addr: 0x26f"
    #fields
    puts "field_name   :AXI1_END_ADDR_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x26f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x26f $data
}

proc mc_0x26f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x26f]

    return $rdata
}

proc mc_AXI1_END_ADDR_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x26f 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x26f 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x270_print {} {
    puts "addr: 0x270"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_13 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x270_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x270 $data
}

proc mc_0x270_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x270]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x270 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x270 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x270 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x270 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x271_print {} {
    puts "addr: 0x271"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_13 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x271_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x271 $data
}

proc mc_0x271_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x271]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x271 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x271 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x271 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x271 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x272_print {} {
    puts "addr: 0x272"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x272_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x272 $data
}

proc mc_0x272_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x272]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x272 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x272 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x273_print {} {
    puts "addr: 0x273"
    #fields
    puts "field_name   :AXI1_START_ADDR_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x273_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x273 $data
}

proc mc_0x273_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x273]

    return $rdata
}

proc mc_AXI1_START_ADDR_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x273 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x273 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x274_print {} {
    puts "addr: 0x274"
    #fields
    puts "field_name   :AXI1_END_ADDR_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x274_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x274 $data
}

proc mc_0x274_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x274]

    return $rdata
}

proc mc_AXI1_END_ADDR_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x274 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x274 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x275_print {} {
    puts "addr: 0x275"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_14 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x275_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x275 $data
}

proc mc_0x275_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x275]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x275 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x275 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x275 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x275 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x276_print {} {
    puts "addr: 0x276"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_14 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x276_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x276 $data
}

proc mc_0x276_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x276]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x276 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x276 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x276 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x276 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x277_print {} {
    puts "addr: 0x277"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x277_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x277 $data
}

proc mc_0x277_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x277]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x277 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x277 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x278_print {} {
    puts "addr: 0x278"
    #fields
    puts "field_name   :AXI1_START_ADDR_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x0 "
} 

proc mc_0x278_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x278 $data
}

proc mc_0x278_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x278]

    return $rdata
}

proc mc_AXI1_START_ADDR_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x278 0 25 $data 
} 
 
proc mc_AXI1_START_ADDR_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x278 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x279_print {} {
    puts "addr: 0x279"
    #fields
    puts "field_name   :AXI1_END_ADDR_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :25 "
    puts "default field_value  :0x1ffffff "
} 

proc mc_0x279_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x279 $data
}

proc mc_0x279_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x279]

    return $rdata
}

proc mc_AXI1_END_ADDR_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x279 0 25 $data 
} 
 
proc mc_AXI1_END_ADDR_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x279 0 25 ] 

    return $rdata 
}

#################################

proc mc_0x27a_print {} {
    puts "addr: 0x27a"
    #fields
    puts "field_name   :AXI1_RANGE_PROT_BITS_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_15 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
} 

proc mc_0x27a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x27a $data
}

proc mc_0x27a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x27a]

    return $rdata
}

proc mc_AXI1_RANGE_PROT_BITS_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x27a 0 2 $data 
} 
 
proc mc_AXI1_RANGE_PROT_BITS_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x27a 0 2 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x27a 8 16 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x27a 8 16 ] 

    return $rdata 
}

#################################

proc mc_0x27b_print {} {
    puts "addr: 0x27b"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0xffff "
    puts "field_name   :AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_15 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x27b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x27b $data
}

proc mc_0x27b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x27b]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x27b 0 16 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x27b 0 16 ] 

    return $rdata 
}

proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x27b 16 14 $data 
} 
 
proc mc_AXI1_RANGE_RID_CHECK_BITS_ID_LOOKUP_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x27b 16 14 ] 

    return $rdata 
}

#################################

proc mc_0x27c_print {} {
    puts "addr: 0x27c"
    #fields
    puts "field_name   :AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0xf "
} 

proc mc_0x27c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x27c $data
}

proc mc_0x27c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x27c]

    return $rdata
}

proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x27c 0 14 $data 
} 
 
proc mc_AXI1_RANGE_WID_CHECK_BITS_ID_LOOKUP_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x27c 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x31c_print {} {
    puts "addr: 0x31c"
    #fields
    puts "field_name   :WEIGHTED_ROUND_ROBIN_LATENCY_CONTROL "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :WEIGHTED_ROUND_ROBIN_WEIGHT_SHARING "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x31c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x31c $data
}

proc mc_0x31c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x31c]

    return $rdata
}

proc mc_WEIGHTED_ROUND_ROBIN_LATENCY_CONTROL_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31c 16 1 $data 
} 
 
proc mc_WEIGHTED_ROUND_ROBIN_LATENCY_CONTROL_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31c 16 1 ] 

    return $rdata 
}

proc mc_WEIGHTED_ROUND_ROBIN_WEIGHT_SHARING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31c 24 1 $data 
} 
 
proc mc_WEIGHTED_ROUND_ROBIN_WEIGHT_SHARING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31c 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x31d_print {} {
    puts "addr: 0x31d"
    #fields
    puts "field_name   :WRR_PARAM_VALUE_ERR "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_PRIORITY0_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :AXI0_PRIORITY1_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :AXI0_PRIORITY2_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
} 

proc mc_0x31d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x31d $data
}

proc mc_0x31d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x31d]

    return $rdata
}

proc mc_WRR_PARAM_VALUE_ERR_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31d 0 4 $data 
} 
 
proc mc_WRR_PARAM_VALUE_ERR_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31d 0 4 ] 

    return $rdata 
}

proc mc_AXI0_PRIORITY0_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31d 8 4 $data 
} 
 
proc mc_AXI0_PRIORITY0_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31d 8 4 ] 

    return $rdata 
}

proc mc_AXI0_PRIORITY1_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31d 16 4 $data 
} 
 
proc mc_AXI0_PRIORITY1_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31d 16 4 ] 

    return $rdata 
}

proc mc_AXI0_PRIORITY2_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31d 24 4 $data 
} 
 
proc mc_AXI0_PRIORITY2_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31d 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x31e_print {} {
    puts "addr: 0x31e"
    #fields
    puts "field_name   :AXI0_PRIORITY3_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :AXI0_PRIORITY4_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :AXI0_PRIORITY5_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :AXI0_PRIORITY6_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
} 

proc mc_0x31e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x31e $data
}

proc mc_0x31e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x31e]

    return $rdata
}

proc mc_AXI0_PRIORITY3_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31e 0 4 $data 
} 
 
proc mc_AXI0_PRIORITY3_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31e 0 4 ] 

    return $rdata 
}

proc mc_AXI0_PRIORITY4_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31e 8 4 $data 
} 
 
proc mc_AXI0_PRIORITY4_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31e 8 4 ] 

    return $rdata 
}

proc mc_AXI0_PRIORITY5_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31e 16 4 $data 
} 
 
proc mc_AXI0_PRIORITY5_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31e 16 4 ] 

    return $rdata 
}

proc mc_AXI0_PRIORITY6_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31e 24 4 $data 
} 
 
proc mc_AXI0_PRIORITY6_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31e 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x31f_print {} {
    puts "addr: 0x31f"
    #fields
    puts "field_name   :AXI0_PRIORITY7_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :AXI0_PORT_ORDERING "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI0_PRIORITY_RELAX "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :10 "
    puts "default field_value  :0x64 "
} 

proc mc_0x31f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x31f $data
}

proc mc_0x31f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x31f]

    return $rdata
}

proc mc_AXI0_PRIORITY7_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31f 0 4 $data 
} 
 
proc mc_AXI0_PRIORITY7_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31f 0 4 ] 

    return $rdata 
}

proc mc_AXI0_PORT_ORDERING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31f 8 1 $data 
} 
 
proc mc_AXI0_PORT_ORDERING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31f 8 1 ] 

    return $rdata 
}

proc mc_AXI0_PRIORITY_RELAX_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x31f 16 10 $data 
} 
 
proc mc_AXI0_PRIORITY_RELAX_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x31f 16 10 ] 

    return $rdata 
}

#################################

proc mc_0x320_print {} {
    puts "addr: 0x320"
    #fields
    puts "field_name   :AXI1_PRIORITY0_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI1_PRIORITY1_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI1_PRIORITY2_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI1_PRIORITY3_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
} 

proc mc_0x320_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x320 $data
}

proc mc_0x320_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x320]

    return $rdata
}

proc mc_AXI1_PRIORITY0_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x320 0 4 $data 
} 
 
proc mc_AXI1_PRIORITY0_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x320 0 4 ] 

    return $rdata 
}

proc mc_AXI1_PRIORITY1_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x320 8 4 $data 
} 
 
proc mc_AXI1_PRIORITY1_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x320 8 4 ] 

    return $rdata 
}

proc mc_AXI1_PRIORITY2_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x320 16 4 $data 
} 
 
proc mc_AXI1_PRIORITY2_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x320 16 4 ] 

    return $rdata 
}

proc mc_AXI1_PRIORITY3_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x320 24 4 $data 
} 
 
proc mc_AXI1_PRIORITY3_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x320 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x321_print {} {
    puts "addr: 0x321"
    #fields
    puts "field_name   :AXI1_PRIORITY4_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI1_PRIORITY5_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI1_PRIORITY6_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI1_PRIORITY7_RELATIVE_PRIORITY "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
} 

proc mc_0x321_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x321 $data
}

proc mc_0x321_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x321]

    return $rdata
}

proc mc_AXI1_PRIORITY4_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x321 0 4 $data 
} 
 
proc mc_AXI1_PRIORITY4_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x321 0 4 ] 

    return $rdata 
}

proc mc_AXI1_PRIORITY5_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x321 8 4 $data 
} 
 
proc mc_AXI1_PRIORITY5_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x321 8 4 ] 

    return $rdata 
}

proc mc_AXI1_PRIORITY6_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x321 16 4 $data 
} 
 
proc mc_AXI1_PRIORITY6_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x321 16 4 ] 

    return $rdata 
}

proc mc_AXI1_PRIORITY7_RELATIVE_PRIORITY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x321 24 4 $data 
} 
 
proc mc_AXI1_PRIORITY7_RELATIVE_PRIORITY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x321 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x322_print {} {
    puts "addr: 0x322"
    #fields
    puts "field_name   :AXI1_PORT_ORDERING "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :AXI1_PRIORITY_RELAX "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :10 "
    puts "default field_value  :0x64 "
} 

proc mc_0x322_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x322 $data
}

proc mc_0x322_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x322]

    return $rdata
}

proc mc_AXI1_PORT_ORDERING_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x322 0 1 $data 
} 
 
proc mc_AXI1_PORT_ORDERING_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x322 0 1 ] 

    return $rdata 
}

proc mc_AXI1_PRIORITY_RELAX_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x322 8 10 $data 
} 
 
proc mc_AXI1_PRIORITY_RELAX_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x322 8 10 ] 

    return $rdata 
}

#################################

proc mc_0x328_print {} {
    puts "addr: 0x328"
    #fields
    puts "field_name   :CKE_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :16 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :MEM_RST_VALID "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x328_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x328 $data
}

proc mc_0x328_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x328]

    return $rdata
}

proc mc_CKE_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x328 16 2 $data 
} 
 
proc mc_CKE_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x328 16 2 ] 

    return $rdata 
}

proc mc_MEM_RST_VALID_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x328 24 1 $data 
} 
 
proc mc_MEM_RST_VALID_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x328 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x329_print {} {
    puts "addr: 0x329"
    #fields
    puts "field_name   :TDFI_PHY_RDLAT_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x4d "
} 

proc mc_0x329_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x329 $data
}

proc mc_0x329_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x329]

    return $rdata
}

proc mc_TDFI_PHY_RDLAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x329 0 9 $data 
} 
 
proc mc_TDFI_PHY_RDLAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x329 0 9 ] 

    return $rdata 
}

#################################

proc mc_0x32a_print {} {
    puts "addr: 0x32a"
    #fields
    puts "field_name   :TDFI_CTRLUPD_MAX_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :21 "
    puts "default field_value  :0x554a "
} 

proc mc_0x32a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x32a $data
}

proc mc_0x32a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x32a]

    return $rdata
}

proc mc_TDFI_CTRLUPD_MAX_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32a 0 21 $data 
} 
 
proc mc_TDFI_CTRLUPD_MAX_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32a 0 21 ] 

    return $rdata 
}

#################################

proc mc_0x32b_print {} {
    puts "addr: 0x32b"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE0_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x32b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x32b $data
}

proc mc_0x32b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x32b]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE0_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32b 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE0_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x32c_print {} {
    puts "addr: 0x32c"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE1_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x32c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x32c $data
}

proc mc_0x32c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x32c]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE1_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32c 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE1_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x32d_print {} {
    puts "addr: 0x32d"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE2_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x32d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x32d $data
}

proc mc_0x32d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x32d]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE2_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32d 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE2_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x32e_print {} {
    puts "addr: 0x32e"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE3_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x32e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x32e $data
}

proc mc_0x32e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x32e]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE3_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32e 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE3_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x32f_print {} {
    puts "addr: 0x32f"
    #fields
    puts "field_name   :TDFI_PHYUPD_RESP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :23 "
    puts "default field_value  :0x17fc6 "
} 

proc mc_0x32f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x32f $data
}

proc mc_0x32f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x32f]

    return $rdata
}

proc mc_TDFI_PHYUPD_RESP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x32f 0 23 $data 
} 
 
proc mc_TDFI_PHYUPD_RESP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x32f 0 23 ] 

    return $rdata 
}

#################################

proc mc_0x330_print {} {
    puts "addr: 0x330"
    #fields
    puts "field_name   :TDFI_CTRLUPD_INTERVAL_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x354d0 "
} 

proc mc_0x330_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x330 $data
}

proc mc_0x330_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x330]

    return $rdata
}

proc mc_TDFI_CTRLUPD_INTERVAL_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x330 0 32 $data 
} 
 
proc mc_TDFI_CTRLUPD_INTERVAL_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x330 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x331_print {} {
    puts "addr: 0x331"
    #fields
    puts "field_name   :TDFI_CTRL_DELAY_F0 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x6 "
    puts "field_name   :TDFI_PHY_WRDATA_F0 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x4 "
    puts "field_name   :TDFI_RDCSLAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x29 "
} 

proc mc_0x331_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x331 $data
}

proc mc_0x331_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x331]

    return $rdata
}

proc mc_TDFI_CTRL_DELAY_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x331 0 4 $data 
} 
 
proc mc_TDFI_CTRL_DELAY_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x331 0 4 ] 

    return $rdata 
}

proc mc_TDFI_PHY_WRDATA_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x331 8 3 $data 
} 
 
proc mc_TDFI_PHY_WRDATA_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x331 8 3 ] 

    return $rdata 
}

proc mc_TDFI_RDCSLAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x331 16 9 $data 
} 
 
proc mc_TDFI_RDCSLAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x331 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x332_print {} {
    puts "addr: 0x332"
    #fields
    puts "field_name   :TDFI_RDDATA_EN_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x14 "
    puts "field_name   :TDFI_WRCSLAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x24 "
} 

proc mc_0x332_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x332 $data
}

proc mc_0x332_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x332]

    return $rdata
}

proc mc_TDFI_RDDATA_EN_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x332 0 9 $data 
} 
 
proc mc_TDFI_RDDATA_EN_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x332 0 9 ] 

    return $rdata 
}

proc mc_TDFI_WRCSLAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x332 16 9 $data 
} 
 
proc mc_TDFI_WRCSLAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x332 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x333_print {} {
    puts "addr: 0x333"
    #fields
    puts "field_name   :TDFI_PHY_WRLAT_F0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x27 "
    puts "field_name   :TDFI_CTRLMSG_RESP_F0 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :7 "
    puts "default field_value  :0x24 "
} 

proc mc_0x333_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x333 $data
}

proc mc_0x333_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x333]

    return $rdata
}

proc mc_TDFI_PHY_WRLAT_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x333 0 9 $data 
} 
 
proc mc_TDFI_PHY_WRLAT_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x333 0 9 ] 

    return $rdata 
}

proc mc_TDFI_CTRLMSG_RESP_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x333 16 7 $data 
} 
 
proc mc_TDFI_CTRLMSG_RESP_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x333 16 7 ] 

    return $rdata 
}

#################################

proc mc_0x334_print {} {
    puts "addr: 0x334"
    #fields
    puts "field_name   :TDFI_PHY_RDLAT_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x4d "
} 

proc mc_0x334_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x334 $data
}

proc mc_0x334_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x334]

    return $rdata
}

proc mc_TDFI_PHY_RDLAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x334 0 9 $data 
} 
 
proc mc_TDFI_PHY_RDLAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x334 0 9 ] 

    return $rdata 
}

#################################

proc mc_0x335_print {} {
    puts "addr: 0x335"
    #fields
    puts "field_name   :TDFI_CTRLUPD_MAX_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :21 "
    puts "default field_value  :0x554a "
} 

proc mc_0x335_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x335 $data
}

proc mc_0x335_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x335]

    return $rdata
}

proc mc_TDFI_CTRLUPD_MAX_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x335 0 21 $data 
} 
 
proc mc_TDFI_CTRLUPD_MAX_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x335 0 21 ] 

    return $rdata 
}

#################################

proc mc_0x336_print {} {
    puts "addr: 0x336"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE0_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x336_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x336 $data
}

proc mc_0x336_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x336]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE0_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x336 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE0_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x336 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x337_print {} {
    puts "addr: 0x337"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE1_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x337_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x337 $data
}

proc mc_0x337_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x337]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE1_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x337 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE1_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x337 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x338_print {} {
    puts "addr: 0x338"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE2_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x338_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x338 $data
}

proc mc_0x338_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x338]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE2_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x338 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE2_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x338 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x339_print {} {
    puts "addr: 0x339"
    #fields
    puts "field_name   :TDFI_PHYUPD_TYPE3_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x200 "
} 

proc mc_0x339_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x339 $data
}

proc mc_0x339_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x339]

    return $rdata
}

proc mc_TDFI_PHYUPD_TYPE3_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x339 0 32 $data 
} 
 
proc mc_TDFI_PHYUPD_TYPE3_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x339 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x33a_print {} {
    puts "addr: 0x33a"
    #fields
    puts "field_name   :TDFI_PHYUPD_RESP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :23 "
    puts "default field_value  :0x17fc6 "
} 

proc mc_0x33a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x33a $data
}

proc mc_0x33a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x33a]

    return $rdata
}

proc mc_TDFI_PHYUPD_RESP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33a 0 23 $data 
} 
 
proc mc_TDFI_PHYUPD_RESP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33a 0 23 ] 

    return $rdata 
}

#################################

proc mc_0x33b_print {} {
    puts "addr: 0x33b"
    #fields
    puts "field_name   :TDFI_CTRLUPD_INTERVAL_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x354d0 "
} 

proc mc_0x33b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x33b $data
}

proc mc_0x33b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x33b]

    return $rdata
}

proc mc_TDFI_CTRLUPD_INTERVAL_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33b 0 32 $data 
} 
 
proc mc_TDFI_CTRLUPD_INTERVAL_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x33c_print {} {
    puts "addr: 0x33c"
    #fields
    puts "field_name   :TDFI_CTRL_DELAY_F1 "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x6 "
    puts "field_name   :TDFI_PHY_WRDATA_F1 "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x4 "
    puts "field_name   :TDFI_RDCSLAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x29 "
} 

proc mc_0x33c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x33c $data
}

proc mc_0x33c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x33c]

    return $rdata
}

proc mc_TDFI_CTRL_DELAY_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33c 0 4 $data 
} 
 
proc mc_TDFI_CTRL_DELAY_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33c 0 4 ] 

    return $rdata 
}

proc mc_TDFI_PHY_WRDATA_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33c 8 3 $data 
} 
 
proc mc_TDFI_PHY_WRDATA_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33c 8 3 ] 

    return $rdata 
}

proc mc_TDFI_RDCSLAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33c 16 9 $data 
} 
 
proc mc_TDFI_RDCSLAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33c 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x33d_print {} {
    puts "addr: 0x33d"
    #fields
    puts "field_name   :TDFI_RDDATA_EN_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x14 "
    puts "field_name   :TDFI_WRCSLAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :9 "
    puts "default field_value  :0x24 "
} 

proc mc_0x33d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x33d $data
}

proc mc_0x33d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x33d]

    return $rdata
}

proc mc_TDFI_RDDATA_EN_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33d 0 9 $data 
} 
 
proc mc_TDFI_RDDATA_EN_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33d 0 9 ] 

    return $rdata 
}

proc mc_TDFI_WRCSLAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33d 16 9 $data 
} 
 
proc mc_TDFI_WRCSLAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33d 16 9 ] 

    return $rdata 
}

#################################

proc mc_0x33e_print {} {
    puts "addr: 0x33e"
    #fields
    puts "field_name   :TDFI_PHY_WRLAT_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x27 "
    puts "field_name   :TDFI_CTRLMSG_RESP_F1 "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :7 "
    puts "default field_value  :0x24 "
} 

proc mc_0x33e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x33e $data
}

proc mc_0x33e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x33e]

    return $rdata
}

proc mc_TDFI_PHY_WRLAT_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33e 0 9 $data 
} 
 
proc mc_TDFI_PHY_WRLAT_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33e 0 9 ] 

    return $rdata 
}

proc mc_TDFI_CTRLMSG_RESP_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33e 16 7 $data 
} 
 
proc mc_TDFI_CTRLMSG_RESP_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33e 16 7 ] 

    return $rdata 
}

#################################

proc mc_0x33f_print {} {
    puts "addr: 0x33f"
    #fields
    puts "field_name   :DLL_RST_DELAY "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :16 "
    puts "default field_value  :0x0 "
    puts "field_name   :DLL_RST_ADJ_DLY "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :UPDATE_ERROR_STATUS "
    puts "field_access :RD "
    puts "field_bitpos :24 "
    puts "field_size   :7 "
    puts "default field_value  :0x0 "
} 

proc mc_0x33f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x33f $data
}

proc mc_0x33f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x33f]

    return $rdata
}

proc mc_DLL_RST_DELAY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33f 0 16 $data 
} 
 
proc mc_DLL_RST_DELAY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33f 0 16 ] 

    return $rdata 
}

proc mc_DLL_RST_ADJ_DLY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33f 16 8 $data 
} 
 
proc mc_DLL_RST_ADJ_DLY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33f 16 8 ] 

    return $rdata 
}

proc mc_UPDATE_ERROR_STATUS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x33f 24 7 $data 
} 
 
proc mc_UPDATE_ERROR_STATUS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x33f 24 7 ] 

    return $rdata 
}

#################################

proc mc_0x340_print {} {
    puts "addr: 0x340"
    #fields
    puts "field_name   :DRAM_CLK_DISABLE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :TDFI_CTRLUPD_MIN "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :16 "
    puts "default field_value  :0xc "
    puts "field_name   :TDFI_DRAM_CLK_DISABLE "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x9 "
} 

proc mc_0x340_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x340 $data
}

proc mc_0x340_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x340]

    return $rdata
}

proc mc_DRAM_CLK_DISABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x340 0 2 $data 
} 
 
proc mc_DRAM_CLK_DISABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x340 0 2 ] 

    return $rdata 
}

proc mc_TDFI_CTRLUPD_MIN_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x340 8 16 $data 
} 
 
proc mc_TDFI_CTRLUPD_MIN_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x340 8 16 ] 

    return $rdata 
}

proc mc_TDFI_DRAM_CLK_DISABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x340 24 4 $data 
} 
 
proc mc_TDFI_DRAM_CLK_DISABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x340 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x341_print {} {
    puts "addr: 0x341"
    #fields
    puts "field_name   :TDFI_DRAM_CLK_ENABLE "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0xd "
    puts "field_name   :TDFI_PARIN_LAT "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
    puts "field_name   :TDFI_WRDATA_DELAY "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :8 "
    puts "default field_value  :0x9 "
    puts "field_name   :EN_1T_TIMING_F0 "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
} 

proc mc_0x341_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x341 $data
}

proc mc_0x341_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x341]

    return $rdata
}

proc mc_TDFI_DRAM_CLK_ENABLE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x341 0 4 $data 
} 
 
proc mc_TDFI_DRAM_CLK_ENABLE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x341 0 4 ] 

    return $rdata 
}

proc mc_TDFI_PARIN_LAT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x341 8 3 $data 
} 
 
proc mc_TDFI_PARIN_LAT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x341 8 3 ] 

    return $rdata 
}

proc mc_TDFI_WRDATA_DELAY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x341 16 8 $data 
} 
 
proc mc_TDFI_WRDATA_DELAY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x341 16 8 ] 

    return $rdata 
}

proc mc_EN_1T_TIMING_F0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x341 24 1 $data 
} 
 
proc mc_EN_1T_TIMING_F0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x341 24 1 ] 

    return $rdata 
}

#################################

proc mc_0x342_print {} {
    puts "addr: 0x342"
    #fields
    puts "field_name   :EN_1T_TIMING_F1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :DISABLE_MEMORY_MASKED_WRITE "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :CS_PHASE_2N "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x1 "
} 

proc mc_0x342_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x342 $data
}

proc mc_0x342_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x342]

    return $rdata
}

proc mc_EN_1T_TIMING_F1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x342 0 1 $data 
} 
 
proc mc_EN_1T_TIMING_F1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x342 0 1 ] 

    return $rdata 
}

proc mc_DISABLE_MEMORY_MASKED_WRITE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x342 8 1 $data 
} 
 
proc mc_DISABLE_MEMORY_MASKED_WRITE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x342 8 1 ] 

    return $rdata 
}

proc mc_CS_PHASE_2N_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x342 16 1 $data 
} 
 
proc mc_CS_PHASE_2N_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x342 16 1 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x342 24 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x342 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x343_print {} {
    puts "addr: 0x343"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :3 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :3 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :3 "
    puts "default field_value  :0x1 "
} 

proc mc_0x343_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x343 $data
}

proc mc_0x343_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x343]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x343 0 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x343 0 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x343 8 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x343 8 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x343 16 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x343 16 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x343 24 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x343 24 3 ] 

    return $rdata 
}

#################################

proc mc_0x344_print {} {
    puts "addr: 0x344"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :3 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
} 

proc mc_0x344_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x344 $data
}

proc mc_0x344_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x344]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x344 0 3 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x344 0 3 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x344 8 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x344 8 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x344 16 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x344 16 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x344 24 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x344 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x345_print {} {
    puts "addr: 0x345"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
} 

proc mc_0x345_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x345 $data
}

proc mc_0x345_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x345]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x345 0 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x345 0 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x345 8 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x345 8 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x345 16 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x345 16 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x345 24 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x345 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x346_print {} {
    puts "addr: 0x346"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
} 

proc mc_0x346_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x346 $data
}

proc mc_0x346_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x346]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x346 0 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x346 0 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x346 8 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x346 8 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x346 16 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x346 16 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x346 24 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x346 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x347_print {} {
    puts "addr: 0x347"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x2 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
} 

proc mc_0x347_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x347 $data
}

proc mc_0x347_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x347]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x347 0 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x347 0 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x347 8 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x347 8 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x347 16 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x347 16 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x347 24 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x347 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x348_print {} {
    puts "addr: 0x348"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :16 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :24 "
    puts "field_size   :4 "
    puts "default field_value  :0x1 "
} 

proc mc_0x348_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x348 $data
}

proc mc_0x348_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x348]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x348 0 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x348 0 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x348 8 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x348 8 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x348 16 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x348 16 4 ] 

    return $rdata 
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x348 24 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x348 24 4 ] 

    return $rdata 
}

#################################

proc mc_0x349_print {} {
    puts "addr: 0x349"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW_D "
    puts "field_bitpos :0 "
    puts "field_size   :4 "
    puts "default field_value  :0x0 "
    puts "field_name   :SRAM_READ_LATENCY "
    puts "field_access :RW_D "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x2 "
    puts "field_name   :CTRL_MULTI_CHANNEL_MODE "
    puts "field_access :RW "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x1 "
    puts "field_name   :CTRL_MULTI_CHANNEL_MAP "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :2 "
    puts "default field_value  :0x3 "
} 

proc mc_0x349_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x349 $data
}

proc mc_0x349_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x349]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x349 0 4 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x349 0 4 ] 

    return $rdata 
}

proc mc_SRAM_READ_LATENCY_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x349 8 2 $data 
} 
 
proc mc_SRAM_READ_LATENCY_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x349 8 2 ] 

    return $rdata 
}

proc mc_CTRL_MULTI_CHANNEL_MODE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x349 16 1 $data 
} 
 
proc mc_CTRL_MULTI_CHANNEL_MODE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x349 16 1 ] 

    return $rdata 
}

proc mc_CTRL_MULTI_CHANNEL_MAP_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x349 24 2 $data 
} 
 
proc mc_CTRL_MULTI_CHANNEL_MAP_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x349 24 2 ] 

    return $rdata 
}

#################################

proc mc_0x34a_print {} {
    puts "addr: 0x34a"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :9 "
    puts "default field_value  :0x0 "
    puts "field_name   :RDIMM_CWW_REQ "
    puts "field_access :WR "
    puts "field_bitpos :16 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
    puts "field_name   :RDIMM_CW_VALUE "
    puts "field_access :RW "
    puts "field_bitpos :24 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x34a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x34a $data
}

proc mc_0x34a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x34a]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34a 0 9 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34a 0 9 ] 

    return $rdata 
}

proc mc_RDIMM_CWW_REQ_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34a 16 1 $data 
} 
 
proc mc_RDIMM_CWW_REQ_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34a 16 1 ] 

    return $rdata 
}

proc mc_RDIMM_CW_VALUE_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34a 24 8 $data 
} 
 
proc mc_RDIMM_CW_VALUE_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34a 24 8 ] 

    return $rdata 
}

#################################

proc mc_0x34b_print {} {
    puts "addr: 0x34b"
    #fields
    puts "field_name   :RDIMM_CW_NUM "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :RDIMM_CW_CS "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x1 "
} 

proc mc_0x34b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x34b $data
}

proc mc_0x34b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x34b]

    return $rdata
}

proc mc_RDIMM_CW_NUM_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34b 0 8 $data 
} 
 
proc mc_RDIMM_CW_NUM_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34b 0 8 ] 

    return $rdata 
}

proc mc_RDIMM_CW_CS_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34b 8 2 $data 
} 
 
proc mc_RDIMM_CW_CS_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34b 8 2 ] 

    return $rdata 
}

#################################

proc mc_0x34c_print {} {
    puts "addr: 0x34c"
    #fields
    puts "field_name   :CA_PARITY_ERROR_INJECT_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x34c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x34c $data
}

proc mc_0x34c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x34c]

    return $rdata
}

proc mc_CA_PARITY_ERROR_INJECT_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34c 0 32 $data 
} 
 
proc mc_CA_PARITY_ERROR_INJECT_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x34d_print {} {
    puts "addr: 0x34d"
    #fields
    puts "field_name   :CA_PARITY_ERROR_INJECT_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :14 "
    puts "default field_value  :0x0 "
} 

proc mc_0x34d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x34d $data
}

proc mc_0x34d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x34d]

    return $rdata
}

proc mc_CA_PARITY_ERROR_INJECT_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34d 0 14 $data 
} 
 
proc mc_CA_PARITY_ERROR_INJECT_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34d 0 14 ] 

    return $rdata 
}

#################################

proc mc_0x34e_print {} {
    puts "addr: 0x34e"
    #fields
    puts "field_name   :PPR_DATA_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x34e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x34e $data
}

proc mc_0x34e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x34e]

    return $rdata
}

proc mc_PPR_DATA_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34e 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x34f_print {} {
    puts "addr: 0x34f"
    #fields
    puts "field_name   :PPR_DATA_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x34f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x34f $data
}

proc mc_0x34f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x34f]

    return $rdata
}

proc mc_PPR_DATA_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x34f 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x34f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x350_print {} {
    puts "addr: 0x350"
    #fields
    puts "field_name   :PPR_DATA_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x350_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x350 $data
}

proc mc_0x350_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x350]

    return $rdata
}

proc mc_PPR_DATA_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x350 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x350 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x351_print {} {
    puts "addr: 0x351"
    #fields
    puts "field_name   :PPR_DATA_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x351_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x351 $data
}

proc mc_0x351_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x351]

    return $rdata
}

proc mc_PPR_DATA_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x351 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x351 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x352_print {} {
    puts "addr: 0x352"
    #fields
    puts "field_name   :PPR_DATA_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x352_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x352 $data
}

proc mc_0x352_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x352]

    return $rdata
}

proc mc_PPR_DATA_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x352 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x352 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x353_print {} {
    puts "addr: 0x353"
    #fields
    puts "field_name   :PPR_DATA_PART_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x353_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x353 $data
}

proc mc_0x353_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x353]

    return $rdata
}

proc mc_PPR_DATA_PART_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x353 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x353 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x354_print {} {
    puts "addr: 0x354"
    #fields
    puts "field_name   :PPR_DATA_PART_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x354_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x354 $data
}

proc mc_0x354_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x354]

    return $rdata
}

proc mc_PPR_DATA_PART_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x354 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x354 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x355_print {} {
    puts "addr: 0x355"
    #fields
    puts "field_name   :PPR_DATA_PART_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x355_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x355 $data
}

proc mc_0x355_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x355]

    return $rdata
}

proc mc_PPR_DATA_PART_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x355 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x355 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x356_print {} {
    puts "addr: 0x356"
    #fields
    puts "field_name   :PPR_DATA_PART_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x356_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x356 $data
}

proc mc_0x356_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x356]

    return $rdata
}

proc mc_PPR_DATA_PART_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x356 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x356 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x357_print {} {
    puts "addr: 0x357"
    #fields
    puts "field_name   :PPR_DATA_PART_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x357_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x357 $data
}

proc mc_0x357_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x357]

    return $rdata
}

proc mc_PPR_DATA_PART_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x357 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x357 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x358_print {} {
    puts "addr: 0x358"
    #fields
    puts "field_name   :PPR_DATA_PART_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x358_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x358 $data
}

proc mc_0x358_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x358]

    return $rdata
}

proc mc_PPR_DATA_PART_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x358 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x358 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x359_print {} {
    puts "addr: 0x359"
    #fields
    puts "field_name   :PPR_DATA_PART_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x359_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x359 $data
}

proc mc_0x359_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x359]

    return $rdata
}

proc mc_PPR_DATA_PART_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x359 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x359 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x35a_print {} {
    puts "addr: 0x35a"
    #fields
    puts "field_name   :PPR_DATA_PART_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x35a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x35a $data
}

proc mc_0x35a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x35a]

    return $rdata
}

proc mc_PPR_DATA_PART_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35a 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x35b_print {} {
    puts "addr: 0x35b"
    #fields
    puts "field_name   :PPR_DATA_PART_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x35b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x35b $data
}

proc mc_0x35b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x35b]

    return $rdata
}

proc mc_PPR_DATA_PART_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35b 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x35c_print {} {
    puts "addr: 0x35c"
    #fields
    puts "field_name   :PPR_DATA_PART_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x35c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x35c $data
}

proc mc_0x35c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x35c]

    return $rdata
}

proc mc_PPR_DATA_PART_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35c 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x35d_print {} {
    puts "addr: 0x35d"
    #fields
    puts "field_name   :PPR_DATA_PART_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x35d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x35d $data
}

proc mc_0x35d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x35d]

    return $rdata
}

proc mc_PPR_DATA_PART_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35d 0 32 $data 
} 
 
proc mc_PPR_DATA_PART_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x35e_print {} {
    puts "addr: 0x35e"
    #fields
    puts "field_name   :PPR_ECC_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x35e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x35e $data
}

proc mc_0x35e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x35e]

    return $rdata
}

proc mc_PPR_ECC_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35e 0 32 $data 
} 
 
proc mc_PPR_ECC_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x35f_print {} {
    puts "addr: 0x35f"
    #fields
    puts "field_name   :PPR_ECC_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x35f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x35f $data
}

proc mc_0x35f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x35f]

    return $rdata
}

proc mc_PPR_ECC_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x35f 0 32 $data 
} 
 
proc mc_PPR_ECC_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x35f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x360_print {} {
    puts "addr: 0x360"
    #fields
    puts "field_name   :AUTO_TEMPCHK_VAL_0_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x360_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x360 $data
}

proc mc_0x360_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x360]

    return $rdata
}

proc mc_AUTO_TEMPCHK_VAL_0_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x360 0 32 $data 
} 
 
proc mc_AUTO_TEMPCHK_VAL_0_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x360 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x361_print {} {
    puts "addr: 0x361"
    #fields
    puts "field_name   :AUTO_TEMPCHK_VAL_0_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x361_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x361 $data
}

proc mc_0x361_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x361]

    return $rdata
}

proc mc_AUTO_TEMPCHK_VAL_0_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x361 0 32 $data 
} 
 
proc mc_AUTO_TEMPCHK_VAL_0_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x361 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x362_print {} {
    puts "addr: 0x362"
    #fields
    puts "field_name   :AUTO_TEMPCHK_VAL_0_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
} 

proc mc_0x362_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x362 $data
}

proc mc_0x362_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x362]

    return $rdata
}

proc mc_AUTO_TEMPCHK_VAL_0_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x362 0 8 $data 
} 
 
proc mc_AUTO_TEMPCHK_VAL_0_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x362 0 8 ] 

    return $rdata 
}

#################################

proc mc_0x363_print {} {
    puts "addr: 0x363"
    #fields
    puts "field_name   :AUTO_TEMPCHK_VAL_1_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x363_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x363 $data
}

proc mc_0x363_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x363]

    return $rdata
}

proc mc_AUTO_TEMPCHK_VAL_1_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x363 0 32 $data 
} 
 
proc mc_AUTO_TEMPCHK_VAL_1_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x363 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x364_print {} {
    puts "addr: 0x364"
    #fields
    puts "field_name   :AUTO_TEMPCHK_VAL_1_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x364_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x364 $data
}

proc mc_0x364_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x364]

    return $rdata
}

proc mc_AUTO_TEMPCHK_VAL_1_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x364 0 32 $data 
} 
 
proc mc_AUTO_TEMPCHK_VAL_1_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x364 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x365_print {} {
    puts "addr: 0x365"
    #fields
    puts "field_name   :AUTO_TEMPCHK_VAL_1_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :8 "
    puts "default field_value  :0x0 "
    puts "field_name   :BIST_RESULT "
    puts "field_access :RD "
    puts "field_bitpos :8 "
    puts "field_size   :1 "
    puts "default field_value  :0x0 "
} 

proc mc_0x365_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x365 $data
}

proc mc_0x365_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x365]

    return $rdata
}

proc mc_AUTO_TEMPCHK_VAL_1_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x365 0 8 $data 
} 
 
proc mc_AUTO_TEMPCHK_VAL_1_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x365 0 8 ] 

    return $rdata 
}

proc mc_BIST_RESULT_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x365 8 1 $data 
} 
 
proc mc_BIST_RESULT_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x365 8 1 ] 

    return $rdata 
}

#################################

proc mc_0x366_print {} {
    puts "addr: 0x366"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x366_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x366 $data
}

proc mc_0x366_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x366]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x366 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x366 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x367_print {} {
    puts "addr: 0x367"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x367_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x367 $data
}

proc mc_0x367_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x367]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x367 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x367 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x368_print {} {
    puts "addr: 0x368"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x368_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x368 $data
}

proc mc_0x368_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x368]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x368 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x368 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x369_print {} {
    puts "addr: 0x369"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x369_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x369 $data
}

proc mc_0x369_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x369]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x369 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x369 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x36a_print {} {
    puts "addr: 0x36a"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x36a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x36a $data
}

proc mc_0x36a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x36a]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36a 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x36b_print {} {
    puts "addr: 0x36b"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x36b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x36b $data
}

proc mc_0x36b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x36b]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36b 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x36c_print {} {
    puts "addr: 0x36c"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x36c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x36c $data
}

proc mc_0x36c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x36c]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36c 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x36d_print {} {
    puts "addr: 0x36d"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x36d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x36d $data
}

proc mc_0x36d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x36d]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36d 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x36e_print {} {
    puts "addr: 0x36e"
    #fields
    puts "field_name   :BIST_DATA_MASK_PART_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x36e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x36e $data
}

proc mc_0x36e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x36e]

    return $rdata
}

proc mc_BIST_DATA_MASK_PART_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36e 0 32 $data 
} 
 
proc mc_BIST_DATA_MASK_PART_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x36f_print {} {
    puts "addr: 0x36f"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_0 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x36f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x36f $data
}

proc mc_0x36f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x36f]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x36f 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x36f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x370_print {} {
    puts "addr: 0x370"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_1 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x370_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x370 $data
}

proc mc_0x370_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x370]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x370 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x370 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x371_print {} {
    puts "addr: 0x371"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_2 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x371_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x371 $data
}

proc mc_0x371_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x371]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x371 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x371 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x372_print {} {
    puts "addr: 0x372"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_3 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x372_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x372 $data
}

proc mc_0x372_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x372]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x372 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x372 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x373_print {} {
    puts "addr: 0x373"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_4 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x373_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x373 $data
}

proc mc_0x373_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x373]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x373 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x373 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x374_print {} {
    puts "addr: 0x374"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_5 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x374_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x374 $data
}

proc mc_0x374_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x374]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x374 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x374 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x375_print {} {
    puts "addr: 0x375"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_6 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x375_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x375 $data
}

proc mc_0x375_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x375]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x375 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x375 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x376_print {} {
    puts "addr: 0x376"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_7 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x376_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x376 $data
}

proc mc_0x376_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x376]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x376 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x376 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x377_print {} {
    puts "addr: 0x377"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_8 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x377_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x377 $data
}

proc mc_0x377_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x377]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x377 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x377 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x378_print {} {
    puts "addr: 0x378"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_9 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x378_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x378 $data
}

proc mc_0x378_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x378]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x378 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x378 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x379_print {} {
    puts "addr: 0x379"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_10 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x379_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x379 $data
}

proc mc_0x379_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x379]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x379 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x379 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x37a_print {} {
    puts "addr: 0x37a"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_11 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x37a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x37a $data
}

proc mc_0x37a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x37a]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37a 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x37b_print {} {
    puts "addr: 0x37b"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_12 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x37b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x37b $data
}

proc mc_0x37b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x37b]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37b 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x37c_print {} {
    puts "addr: 0x37c"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_13 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x37c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x37c $data
}

proc mc_0x37c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x37c]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37c 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x37d_print {} {
    puts "addr: 0x37d"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_14 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x37d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x37d $data
}

proc mc_0x37d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x37d]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37d 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x37e_print {} {
    puts "addr: 0x37e"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_15 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x37e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x37e $data
}

proc mc_0x37e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x37e]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37e 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x37f_print {} {
    puts "addr: 0x37f"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_16 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x37f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x37f $data
}

proc mc_0x37f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x37f]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_16_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x37f 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_16_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x37f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x380_print {} {
    puts "addr: 0x380"
    #fields
    puts "field_name   :BIST_DATA_PATTERN_PART_17 "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x380_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x380 $data
}

proc mc_0x380_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x380]

    return $rdata
}

proc mc_BIST_DATA_PATTERN_PART_17_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x380 0 32 $data 
} 
 
proc mc_BIST_DATA_PATTERN_PART_17_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x380 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x381_print {} {
    puts "addr: 0x381"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :64 "
    puts "default field_value  :0x0L "
} 

proc mc_0x381_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x381 $data
}

proc mc_0x381_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x381]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x381 0 64 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x381 0 64 ] 

    return $rdata 
}

#################################

proc mc_0x382_print {} {
    puts "addr: 0x382"
    #fields
    puts "field_name   :RESERVED "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :64 "
    puts "default field_value  :0x0L "
} 

proc mc_0x382_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x382 $data
}

proc mc_0x382_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x382]

    return $rdata
}

proc mc_RESERVED_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x382 0 64 $data 
} 
 
proc mc_RESERVED_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x382 0 64 ] 

    return $rdata 
}

#################################

proc mc_0x383_print {} {
    puts "addr: 0x383"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x383_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x383 $data
}

proc mc_0x383_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x383]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x383 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x383 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x384_print {} {
    puts "addr: 0x384"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x384_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x384 $data
}

proc mc_0x384_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x384]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x384 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x384 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x385_print {} {
    puts "addr: 0x385"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x385_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x385 $data
}

proc mc_0x385_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x385]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x385 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x385 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x386_print {} {
    puts "addr: 0x386"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_3 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x386_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x386 $data
}

proc mc_0x386_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x386]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x386 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x386 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x387_print {} {
    puts "addr: 0x387"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_4 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x387_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x387 $data
}

proc mc_0x387_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x387]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x387 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x387 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x388_print {} {
    puts "addr: 0x388"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_5 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x388_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x388 $data
}

proc mc_0x388_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x388]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x388 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x388 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x389_print {} {
    puts "addr: 0x389"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_6 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x389_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x389 $data
}

proc mc_0x389_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x389]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x389 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x389 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x38a_print {} {
    puts "addr: 0x38a"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_7 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x38a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x38a $data
}

proc mc_0x38a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x38a]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38a 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x38b_print {} {
    puts "addr: 0x38b"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_8 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x38b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x38b $data
}

proc mc_0x38b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x38b]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38b 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x38c_print {} {
    puts "addr: 0x38c"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_9 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x38c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x38c $data
}

proc mc_0x38c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x38c]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38c 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x38d_print {} {
    puts "addr: 0x38d"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_10 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x38d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x38d $data
}

proc mc_0x38d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x38d]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38d 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x38e_print {} {
    puts "addr: 0x38e"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_11 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x38e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x38e $data
}

proc mc_0x38e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x38e]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38e 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x38f_print {} {
    puts "addr: 0x38f"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_12 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x38f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x38f $data
}

proc mc_0x38f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x38f]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x38f 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x38f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x390_print {} {
    puts "addr: 0x390"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_13 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x390_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x390 $data
}

proc mc_0x390_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x390]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x390 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x390 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x391_print {} {
    puts "addr: 0x391"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_14 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x391_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x391 $data
}

proc mc_0x391_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x391]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x391 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x391 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x392_print {} {
    puts "addr: 0x392"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_15 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x392_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x392 $data
}

proc mc_0x392_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x392]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x392 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x392 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x393_print {} {
    puts "addr: 0x393"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_16 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x393_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x393 $data
}

proc mc_0x393_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x393]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_16_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x393 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_16_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x393 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x394_print {} {
    puts "addr: 0x394"
    #fields
    puts "field_name   :BIST_EXP_DATA_PART_17 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x394_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x394 $data
}

proc mc_0x394_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x394]

    return $rdata
}

proc mc_BIST_EXP_DATA_PART_17_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x394 0 32 $data 
} 
 
proc mc_BIST_EXP_DATA_PART_17_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x394 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x395_print {} {
    puts "addr: 0x395"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x395_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x395 $data
}

proc mc_0x395_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x395]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x395 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x395 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x396_print {} {
    puts "addr: 0x396"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x396_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x396 $data
}

proc mc_0x396_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x396]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x396 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x396 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x397_print {} {
    puts "addr: 0x397"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x397_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x397 $data
}

proc mc_0x397_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x397]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x397 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x397 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x398_print {} {
    puts "addr: 0x398"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_3 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x398_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x398 $data
}

proc mc_0x398_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x398]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x398 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x398 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x399_print {} {
    puts "addr: 0x399"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_4 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x399_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x399 $data
}

proc mc_0x399_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x399]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x399 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x399 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x39a_print {} {
    puts "addr: 0x39a"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_5 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x39a_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x39a $data
}

proc mc_0x39a_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x39a]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39a 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39a 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x39b_print {} {
    puts "addr: 0x39b"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_6 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x39b_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x39b $data
}

proc mc_0x39b_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x39b]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39b 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39b 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x39c_print {} {
    puts "addr: 0x39c"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_7 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x39c_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x39c $data
}

proc mc_0x39c_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x39c]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39c 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39c 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x39d_print {} {
    puts "addr: 0x39d"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_8 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x39d_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x39d $data
}

proc mc_0x39d_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x39d]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39d 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39d 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x39e_print {} {
    puts "addr: 0x39e"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_9 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x39e_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x39e $data
}

proc mc_0x39e_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x39e]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39e 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39e 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x39f_print {} {
    puts "addr: 0x39f"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_10 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x39f_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x39f $data
}

proc mc_0x39f_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x39f]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x39f 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x39f 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a0_print {} {
    puts "addr: 0x3a0"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_11 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a0 $data
}

proc mc_0x3a0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a0]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a0 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a0 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a1_print {} {
    puts "addr: 0x3a1"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_12 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a1 $data
}

proc mc_0x3a1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a1]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a1 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a1 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a2_print {} {
    puts "addr: 0x3a2"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_13 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a2 $data
}

proc mc_0x3a2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a2]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a2 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a2 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a3_print {} {
    puts "addr: 0x3a3"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_14 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a3 $data
}

proc mc_0x3a3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a3]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a3 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a3 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a4_print {} {
    puts "addr: 0x3a4"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_15 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a4 $data
}

proc mc_0x3a4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a4]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a4 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a4 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a5_print {} {
    puts "addr: 0x3a5"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_16 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a5 $data
}

proc mc_0x3a5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a5]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_16_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a5 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_16_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a5 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a6_print {} {
    puts "addr: 0x3a6"
    #fields
    puts "field_name   :BIST_FAIL_DATA_PART_17 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a6 $data
}

proc mc_0x3a6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a6]

    return $rdata
}

proc mc_BIST_FAIL_DATA_PART_17_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a6 0 32 $data 
} 
 
proc mc_BIST_FAIL_DATA_PART_17_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a6 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a7_print {} {
    puts "addr: 0x3a7"
    #fields
    puts "field_name   :AXI0_FIFO_TYPE_REG "
    puts "field_access :RW "
    puts "field_bitpos :0 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
    puts "field_name   :AXI1_FIFO_TYPE_REG "
    puts "field_access :RW "
    puts "field_bitpos :8 "
    puts "field_size   :2 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a7 $data
}

proc mc_0x3a7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a7]

    return $rdata
}

proc mc_AXI0_FIFO_TYPE_REG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a7 0 2 $data 
} 
 
proc mc_AXI0_FIFO_TYPE_REG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a7 0 2 ] 

    return $rdata 
}

proc mc_AXI1_FIFO_TYPE_REG_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a7 8 2 $data 
} 
 
proc mc_AXI1_FIFO_TYPE_REG_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a7 8 2 ] 

    return $rdata 
}

#################################

proc mc_0x3a8_print {} {
    puts "addr: 0x3a8"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a8 $data
}

proc mc_0x3a8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a8]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a8 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a8 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3a9_print {} {
    puts "addr: 0x3a9"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3a9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3a9 $data
}

proc mc_0x3a9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3a9]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3a9 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3a9 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3aa_print {} {
    puts "addr: 0x3aa"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_2 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3aa_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3aa $data
}

proc mc_0x3aa_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3aa]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_2_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3aa 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_2_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3aa 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3ab_print {} {
    puts "addr: 0x3ab"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_3 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3ab_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3ab $data
}

proc mc_0x3ab_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3ab]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_3_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3ab 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_3_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3ab 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3ac_print {} {
    puts "addr: 0x3ac"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_4 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3ac_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3ac $data
}

proc mc_0x3ac_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3ac]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_4_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3ac 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_4_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3ac 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3ad_print {} {
    puts "addr: 0x3ad"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_5 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3ad_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3ad $data
}

proc mc_0x3ad_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3ad]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_5_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3ad 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_5_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3ad 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3ae_print {} {
    puts "addr: 0x3ae"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_6 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3ae_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3ae $data
}

proc mc_0x3ae_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3ae]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_6_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3ae 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_6_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3ae 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3af_print {} {
    puts "addr: 0x3af"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_7 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3af_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3af $data
}

proc mc_0x3af_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3af]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_7_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3af 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_7_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3af 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b0_print {} {
    puts "addr: 0x3b0"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_8 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b0_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b0 $data
}

proc mc_0x3b0_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b0]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_8_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b0 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_8_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b0 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b1_print {} {
    puts "addr: 0x3b1"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_9 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b1_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b1 $data
}

proc mc_0x3b1_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b1]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_9_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b1 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_9_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b1 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b2_print {} {
    puts "addr: 0x3b2"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_10 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b2_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b2 $data
}

proc mc_0x3b2_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b2]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_10_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b2 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_10_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b2 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b3_print {} {
    puts "addr: 0x3b3"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_11 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b3_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b3 $data
}

proc mc_0x3b3_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b3]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_11_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b3 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_11_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b3 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b4_print {} {
    puts "addr: 0x3b4"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_12 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b4_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b4 $data
}

proc mc_0x3b4_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b4]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_12_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b4 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_12_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b4 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b5_print {} {
    puts "addr: 0x3b5"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_13 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b5_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b5 $data
}

proc mc_0x3b5_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b5]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_13_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b5 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_13_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b5 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b6_print {} {
    puts "addr: 0x3b6"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_14 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b6_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b6 $data
}

proc mc_0x3b6_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b6]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_14_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b6 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_14_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b6 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b7_print {} {
    puts "addr: 0x3b7"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PART_15 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b7_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b7 $data
}

proc mc_0x3b7_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b7]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PART_15_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b7 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PART_15_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b7 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b8_print {} {
    puts "addr: 0x3b8"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PARITY_VECTOR_PART_0 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b8_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b8 $data
}

proc mc_0x3b8_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b8]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PARITY_VECTOR_PART_0_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b8 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PARITY_VECTOR_PART_0_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b8 0 32 ] 

    return $rdata 
}

#################################

proc mc_0x3b9_print {} {
    puts "addr: 0x3b9"
    #fields
    puts "field_name   :PARITY_ERROR_WRITE_DATA_PARITY_VECTOR_PART_1 "
    puts "field_access :RD "
    puts "field_bitpos :0 "
    puts "field_size   :32 "
    puts "default field_value  :0x0 "
} 

proc mc_0x3b9_write_reg { inst_id core_id data } {
    mc_dhs_addr_write  $inst_id $core_id 0x3b9 $data
}

proc mc_0x3b9_read_reg { inst_id core_id  } {
    set rdata [mc_dhs_addr_read $inst_id $core_id 0x3b9]

    return $rdata
}

proc mc_PARITY_ERROR_WRITE_DATA_PARITY_VECTOR_PART_1_write_field { inst_id core_id data } { 
    gig_mc_reg_read_modify_write 0 $inst_id $core_id 0x3b9 0 32 $data 
} 
 
proc mc_PARITY_ERROR_WRITE_DATA_PARITY_VECTOR_PART_1_read_field { inst_id core_id } { 
    set rdata [gig_mc_read_field 0 $inst_id $core_id 0x3b9 0 32 ] 

    return $rdata 
}

