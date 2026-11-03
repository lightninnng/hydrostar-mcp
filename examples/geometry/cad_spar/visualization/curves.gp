reset
set terminal pngcairo size 2400,1540 enhanced font 'Times New Roman,23'
set output '../../../../docs/assets/cad_spar_rao.png'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Curved Spar with a heave plate: Selected headings' font 'Times New Roman,29.7'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/surge.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/surge.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/surge.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/sway.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/sway.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/sway.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/heave.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/heave.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/heave.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/roll.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/roll.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/roll.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key at screen 0.5,0.045 center horizontal maxrows 1 font 'Times New Roman,18.15' samplen 2.2 spacing 1
plot 'data/pitch.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/pitch.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/pitch.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/pitch.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/yaw.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/yaw.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/yaw.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
unset multiplot
unset output
reset
set terminal pdfcairo size 12in,7.7in enhanced font 'Times New Roman,12'
set output '../../../../docs/assets/cad_spar_rao.pdf'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Curved Spar with a heave plate: Selected headings' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/surge.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/surge.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/surge.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/sway.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/sway.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/sway.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/heave.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/heave.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/heave.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/roll.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/roll.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/roll.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key at screen 0.5,0.045 center horizontal maxrows 1 font 'Times New Roman,11' samplen 2.2 spacing 1
plot 'data/pitch.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/pitch.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/pitch.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/pitch.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.2:0.8]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:2 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/yaw.rao' using 1:3 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/yaw.rao' using 1:4 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '120 deg', \
'data/yaw.rao' using 1:5 with linespoints pointtype 7 pointsize 0.5 linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '180 deg'
unset multiplot
unset output
