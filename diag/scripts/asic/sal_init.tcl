set port $slot
set $::slot $slot
set $::port $slot

exec jtag_accpcie_salina clr $slot

diag_close_j2c_if $::port $::slot
diag_open_j2c_if $::port $::slot
diag_close_j2c_if $::port $::slot

after 1000
diag_close_ow_if $::port $::slot
after 1000
diag_open_ow_if $::port $::slot
after 1000
sal_ow_axi

csr_write sal0.ms.ms.cfg_ow 3
after 500
rd sal0.ms.ms.cfg_ow

puts "_msrd"
set rtn [eval _msrd]
puts "_msrd: $rtn"

sal_j2c
