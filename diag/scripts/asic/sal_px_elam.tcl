#  trigge equation = (recovery_recorded == 0x1)
#  recovery_recorded = debug_bus[40]
#  (recovery_recorded==0x1)
#  m0: recovery_recorded == 0x1
#  trigger0: m0 == 1

   # 0 select test_out[511:256]
   # 1 select test_out[255:0]
proc elam_cfg_px {{p 0} {sel 1}} {
   sal_top_elam_clear_cfg 0 0 "px"
   csr_write_field sal0.pxb.pxb.cfg_debug_port enable 1
   csr_write_field sal0.pxb.pxb.cfg_debug_port select 2

   # Turn on the elam chain on all PPs
   csr_write_field sal0.pp.pxc\[0\].cfg_pxc_debug_port daisy_mux_enable 1
   csr_write_field sal0.pp.pxc\[1\].cfg_pxc_debug_port daisy_mux_enable 1
   csr_write_field sal0.pp.pxc\[2\].cfg_pxc_debug_port daisy_mux_enable 1
   csr_write_field sal0.pp.pxc\[3\].cfg_pxc_debug_port daisy_mux_enable 1

   # Select only the guy that you want to see
   csr_write_field sal0.pp.pxc\[$p\].cfg_pxc_debug_port enable 1

   # 0 select test_out[511:256]
   # 1 select test_out[255:0]
   csr_write_field sal0.pp.pxc\[$p\].cfg_pxc_debug_port select $sel

   csr_write_field sal0.pp.pxc\[$p\].cfg_pxc_debug_port daisy_mux_sel 1
   csr_write_field sal0.pp.pxc\[$p\].port_p.cfg_p_debug_port enable 1

   # Keep it 1: 
   csr_write_field sal0.pp.pxc\[$p\].port_p.cfg_p_debug_port select 1

   sal_top_elam_mvec_config 0 0 "px" 0 "vec_ne_value" "96,5,0x10"
   sal_top_elam_trigger 0 0 "px" 0 "vec_ne_0" 0x1 0x0 0x0 0x0
   sal_top_elam_capture_config 0 0 "px" 0 "vec_ne_0" 0x1 0x0 0x0 0x0 0x0 0x0
}

proc elam_arm_px {} {
   csr_write_field sal0.pxb.pxb.pxe.cfg_elam_general rst 1
   csr_write sal0.pxb.pxb.pxe.cfg_elam_general 0
   csr_write_field sal0.pxb.pxb.pxe.cfg_elam_general num_post_sample 256
   csr_write_field sal0.pxb.pxb.pxe.cfg_elam_general arm 1
   csr_write_field sal0.pxb.pxb.pxe.cfg_elam_general rst 0
}

proc elam_sta_px {} {
   puts "num_sample = [csr_read_field sal0.pxb.pxb.pxe.sta_elam num_sample]"
   puts "triggered = [csr_read_field sal0.pxb.pxb.pxe.sta_elam triggered]"
}

proc elam_out_px { {port 0} {sel 1} } {
    csr_write_field sal0.pxb.pxb.pxe.cfg_elam_general stop_sample 1
    csr_write_field sal0.pxb.pxb.pxe.cfg_elam_general arm 0

    if { $sel == 0 } {
        set log_name "elam_port${port}_upper256_bits.log"
        plog_msg "Upper 256 bits: $log_name"
        # This is for upper 256 bits [511:256]
        sal_top_elam_read_buffer                \
            0 0 "px" 0 "                        \
            0,256,'upper256\[511:256\]';        \
            0,2,'rxl0s_n\[257:256\]';           \
            2,2,'txl0s_n\[259:258\]';           \
            4,2,'equ_curr_phase\[261:260\]';    \
            6,1,'lane_reversed\[262\]';         \
            7,1,'timeout\[263\]';               \
            8,1,'chgspeed_ing\[264\]';          \
            9,1,'recovery_direct\[265\]';       \
            10,1,'ltssm_chg\[266\]';            \
            11,1,'ltssm_chg_r_or|equ_phase_chg\[267\]';\
            12,1,'core_is_upstr\[268\]';        \
            13,1,'lksts_receiver_err\[269\]';   \
            14,1,'phystatus_err\[270\]';        \
            15,1,'lksts_link_up\[271\]';        \
            16,8,'detected_lanes\[279:272\]';   \
            24,8,'active_lanes\[287:280\]';     \
            32,6,'polcpl_setnum\[294:288\]';    \
            40,1,'recovery_recorded\[296\]';    \
            41,6,'recovery_reason\[302:297\]';  \
            64,1,'deskew_err\[320\]';           \
            65,6,'framing_err\[326:321\]';      \
            96,16,'pcs_parity_err\[367:352\]';  \
            112,16,'pcs_sync_err\[383:368\]';   \
            128,12,'rx_seq_num\[395:384\]';     \
            140,7,'rx_sta1\[402:396\]';         \
            147,5,'rx_buf_lvl\[407:403\]';      \
            152,5,'rx_sta2\[412:408\]';         \
            160,12,'tx_seq_num\[427:416\]';     \
            172,12,'tx_high_seq_num\[439:428\]';\
            184,14,'tx_sta\[453:440\]';          \
            " $log_name
    } else {
        set log_name "elam_port${port}_lower256_bits.log"
        # This is for lower 256 bits
        plog_msg "Lower 256 bits: $log_name"
        sal_top_elam_read_buffer 0 0 "px" 0 "   \
            0,256,'lower256\[255:0\]';          \
            0,18,'uncor_err\[17:0\]';           \
            18,6,'rsvd\[23:18\]';               \
            24,8,'cor_err\[31:24\]';            \
            32,8,'rsvd\[39:32\]';               \
            40,2,'rcv_cmpl_sta\[41:40\]';       \
            42,6,'rsvd\[47:42\]';               \
            48,12,'rsvd\[59:48\]';              \
            60,1,'enough_credit\[60\]';         \
            61,1,'txbuf_full\[61\]';            \
            62,1,'txbuf_of\[62]';               \
            63,1,'int_tx_req\[63]';             \
            64,26,'rsvd\[89:64\]';              \
            90,6,'l1_sta\[95:90\]';             \
            96,5,'ltssm_state\[100:96\]';       \
            101,1,'dl_active\[101\]';           \
            102,1,'tlp_tx_inhab\[102\]';        \
            103,1,'dllp_tx_inhab\[103\]';       \
            104,4,'lp_sm_sta\[107:104\]';       \
            108,4,'ltssm_chg\[111:108\]';       \
            112,14,'tlp_sta\[125:112\]';        \
            126,2,'rsvd\[127:126\]';            \
            128,255,'rcv_hdr\[255:128\]'        \
            " $log_name
    }
   
}

proc collect_elam_256 { {port 0} {sel 0} } {
    elam_cfg_px $port $sel
    elam_arm_px
    #Then check if it trigger
    elam_sta_px
    ##Then print buffer
    elam_out_px $port $sel
}

proc collect_elam_all {} {
    for {set port 0} { $port < 4} {incr port} {
        for {set sel 0} {$sel < 2} {incr sel} {
            plog_msg "==================="
            plog_msg "port $port; sel: $sel"
            elam_cfg_px $port $sel
            elam_arm_px
            #Then check if it trigger
            elam_sta_px
            ##Then print buffer
            elam_out_px $port $sel
        }
    }
}


#######################################
# elam clear px
# # last arg "bit pos, width, value"
# elam cfg_mvec px 0 vec_ne_value "96,5,0x10"
# elam cfg_trig px 0 vec_ne_0 0x1 0x0 0x0 0x0
# elam capture_config px 0 "vec_ne_0" 0x1 0x0 0x0 0x0 0x0 0x0
# # 0x6000000c: pxb_cfg_debug_port
# # rd sal0.pxb.pxb.cfg_debug_port
# devmem 0x6000000c 32 0x22
# # 0x610a0234: pp_pxc0_cfg_pxc_debug_port
# # rd {sal0.pp.pxc[0].cfg_pxc_debug_port}
# devmem 0x610a0234 32 0x381
# # 0x6108040c: pp_pxc0_port_p_cfg_p_debug_port
# # rd {sal0.pp.pxc[0].port_p.cfg_p_debug_port}
# devmem 0x6108040c 32 0x81
# #sal_top_elam_capture_config 0 0 "px" 0 "vec_ne_0" 0x1 0x0 0x0 0x0 0x0 0x0
# elam arm px
# 
# elam status px
# elam dump px <count>
