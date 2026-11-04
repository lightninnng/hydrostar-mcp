reset
set encoding utf8
set terminal pngcairo size 2400,1540 enhanced font 'Times New Roman,23'
set output '../../../../docs/assets/cad_spar_mesh_comparison.png'
set border linewidth 0.8
set grid back linecolor rgb '#E0E5E9'
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Spar: local sensitivity within 3,000 total panels; heading 60 deg'
set title '(a) Surge'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/surge.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/surge.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(b) Sway'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/sway.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/sway.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(c) Heave'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/heave.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/heave.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(d) Roll'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key off
plot 'data/coarse/roll.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/roll.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(e) Pitch'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key at screen 0.5,0.045 center horizontal font 'Times New Roman,18.15'
plot 'data/coarse/pitch.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/pitch.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(f) Yaw'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key off
plot 'data/coarse/yaw.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/yaw.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
unset multiplot
unset output
reset
set encoding utf8
set terminal pdfcairo size 12in,7.7in enhanced font 'Times New Roman,12'
set output '../../../../docs/assets/cad_spar_mesh_comparison.pdf'
set border linewidth 0.8
set grid back linecolor rgb '#E0E5E9'
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Spar: local sensitivity within 3,000 total panels; heading 60 deg'
set title '(a) Surge'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/surge.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/surge.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(b) Sway'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/sway.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/sway.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(c) Heave'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/heave.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/heave.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(d) Roll'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key off
plot 'data/coarse/roll.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/roll.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(e) Pitch'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key at screen 0.5,0.045 center horizontal font 'Times New Roman,11'
plot 'data/coarse/pitch.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/pitch.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(f) Yaw'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key off
plot 'data/coarse/yaw.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/yaw.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
unset multiplot
unset output
reset
set encoding utf8
set terminal svg size 1400,900 enhanced font 'Times New Roman,15'
set output '../../../../docs/assets/cad_spar_mesh_comparison.svg'
set border linewidth 0.8
set grid back linecolor rgb '#E0E5E9'
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Spar: local sensitivity within 3,000 total panels; heading 60 deg'
set title '(a) Surge'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/surge.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/surge.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(b) Sway'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/sway.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/sway.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(c) Heave'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (m/m)'
set yrange [0:*]
set key off
plot 'data/coarse/heave.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/heave.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(d) Roll'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key off
plot 'data/coarse/roll.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/roll.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(e) Pitch'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key at screen 0.5,0.045 center horizontal font 'Times New Roman,11'
plot 'data/coarse/pitch.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/pitch.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
set title '(f) Yaw'
set xlabel 'Wave frequency (rad/s)'
set ylabel 'RAO (deg/m)'
set yrange [0:*]
set key off
plot 'data/coarse/yaw.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Ring bands (2,916 total)', \
'data/fine/yaw.rao' using 1:3 with linespoints pointtype 9 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Ring bands (2,964 total)'
unset multiplot
unset output
