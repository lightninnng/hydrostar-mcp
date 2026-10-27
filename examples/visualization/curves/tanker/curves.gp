reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-0.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 0 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-0.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 0 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(15))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(15))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(15))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(15))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(15))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(15))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '0 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-30.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 30 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:3 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:3 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:3 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:3 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:3 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:3 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-30.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 30 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(16))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(16))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(16))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(16))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(16))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(16))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '30 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-60.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 60 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:4 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:4 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:4 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:4 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:4 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:4 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-60.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 60 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(17))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(17))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(17))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(17))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(17))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(17))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '60 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-90.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 90 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:5 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:5 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:5 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:5 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:5 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:5 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-90.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 90 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(18))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(18))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(18))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(18))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(18))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(18))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '90 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-120.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 120 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-120.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 120 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(19))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(19))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(19))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(19))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(19))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(19))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '120 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-150.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 150 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:7 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:7 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:7 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:7 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:7 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:7 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-150.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 150 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(20))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(20))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(20))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(20))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(20))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(20))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '150 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-180.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 180 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:8 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:8 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:8 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:8 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:8 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:8 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-180.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 180 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(21))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(21))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(21))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(21))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(21))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(21))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '180 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-210.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 210 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:9 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:9 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:9 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:9 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:9 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:9 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-210.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 210 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(22))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(22))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(22))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(22))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(22))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(22))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '210 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-240.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 240 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:10 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:10 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:10 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:10 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:10 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:10 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-240.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 240 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(23))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(23))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(23))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(23))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(23))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(23))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '240 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-270.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 270 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:11 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:11 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:11 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:11 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:11 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:11 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-270.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 270 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(24))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(24))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(24))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(24))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(24))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(24))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '270 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-300.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 300 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:12 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:12 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:12 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:12 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:12 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:12 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-300.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 300 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(25))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(25))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(25))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(25))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(25))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(25))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '300 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-330.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 330 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:13 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:13 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:13 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:13 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:13 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:13 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-330.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 330 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(26))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(26))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(26))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(26))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(26))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(26))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '330 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-amplitude-360.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 360 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:14 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:14 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:14 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:14 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/pitch.rao' using 1:14 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:14 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
unset multiplot
unset output
reset
set terminal svg size 1400,900 enhanced font 'Times New Roman,15' background rgb 'white'
set output '../../../../docs/assets/tanker-phase-360.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Heading 360 deg' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/surge.rao' using 1:(wrap(column(27))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/sway.rao' using 1:(wrap(column(27))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/heave.rao' using 1:(wrap(column(27))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/roll.rao' using 1:(wrap(column(27))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/pitch.rao' using 1:(wrap(column(27))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'Phase (deg)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [-180:180]
set key off
plot 'data/yaw.rao' using 1:(wrap(column(27))) with points pointtype 7 pointsize 0.32 dashtype 1 linecolor rgb '#0072B2' title '360 deg'
unset multiplot
unset output
reset
set terminal pngcairo size 2400,1540 enhanced font 'Times New Roman,23'
set output '../../../../docs/assets/tanker-response.png'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Selected headings' font 'Times New Roman,29.7'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/surge.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/surge.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/surge.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/surge.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/sway.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/sway.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/sway.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/sway.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/heave.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/heave.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/heave.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/heave.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/roll.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/roll.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/roll.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/roll.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key at screen 0.5,0.045 center horizontal maxrows 1 font 'Times New Roman,18.15' samplen 2.2 spacing 1
plot 'data/pitch.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/pitch.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/pitch.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/pitch.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/pitch.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,23.1'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/yaw.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/yaw.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/yaw.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/yaw.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
unset multiplot
unset output
reset
set terminal pdfcairo size 12in,7.7in enhanced font 'Times New Roman,12'
set output '../../../../docs/assets/tanker-response.pdf'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror scale 0.4
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format x '%g'
set format y '%.3g'
set key off
set samples 100
wrap(x)=x-360.0*floor((x+180.0)/360.0)
set multiplot layout 2,3 rowsfirst margins 0.075,0.98,0.20,0.88 spacing 0.085,0.14 title 'Full-form tanker: Selected headings' font 'Times New Roman,18'
set title '(a) Surge' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/surge.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/surge.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/surge.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/surge.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/surge.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(b) Sway' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/sway.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/sway.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/sway.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/sway.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/sway.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(c) Heave' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (m/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/heave.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/heave.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/heave.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/heave.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/heave.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(d) Roll' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/roll.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/roll.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/roll.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/roll.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/roll.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(e) Pitch' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key at screen 0.5,0.045 center horizontal maxrows 1 font 'Times New Roman,11' samplen 2.2 spacing 1
plot 'data/pitch.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/pitch.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/pitch.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/pitch.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/pitch.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
set title '(f) Yaw' offset 0,-0.1 font 'Times New Roman,14'
set xlabel 'Wave frequency (rad/s)' offset 0,0.35
set ylabel 'RAO (deg/m)' offset 0.5,0
set xrange [0.05:0.6]
set yrange [0:*]
set key off
plot 'data/yaw.rao' using 1:2 with lines linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title '0 deg', \
'data/yaw.rao' using 1:4 with lines linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title '60 deg', \
'data/yaw.rao' using 1:5 with lines linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title '90 deg', \
'data/yaw.rao' using 1:6 with lines linewidth 1.7 dashtype 1 linecolor rgb '#CC79A7' title '120 deg', \
'data/yaw.rao' using 1:8 with lines linewidth 1.7 dashtype 2 linecolor rgb '#4C5966' title '180 deg'
unset multiplot
unset output
