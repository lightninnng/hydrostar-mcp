reset
set terminal svg size 2400,1540 noenhanced font 'Times New Roman,23'
set output '../../../docs/assets/platform-second-order-drift.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format y '%.3g'
set key off
set multiplot layout 2,3 rowsfirst margins 0.08,0.98,0.20,0.84 spacing 0.085,0.18 title 'Semisubmersible: Mean second-order drift loads (60 deg, 200 m depth)' font 'Times New Roman,29.7'
set title '(a) Fx' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Mean drift (kN/m²)'
set xrange [0.39:1.11]
set yrange [*:*]
set key off
plot 'rao/drift_fx_near.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 7 pointsize 0.45 linewidth 1.6 dashtype 1 linecolor rgb '#0072B2' title 'Near field', \
'rao/drift_fx_far.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 8 pointsize 0.45 linewidth 1.6 dashtype 2 linecolor rgb '#D55E00' title 'Far field'
set title '(b) Fy' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Mean drift (kN/m²)'
set xrange [0.39:1.11]
set yrange [*:*]
set key off
plot 'rao/drift_fy_near.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 7 pointsize 0.45 linewidth 1.6 dashtype 1 linecolor rgb '#0072B2' title 'Near field', \
'rao/drift_fy_far.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 8 pointsize 0.45 linewidth 1.6 dashtype 2 linecolor rgb '#D55E00' title 'Far field'
set title '(c) Fz' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Mean drift (kN/m²)'
set xrange [0.39:1.11]
set yrange [*:*]
set key off
plot 'rao/drift_fz_near.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 7 pointsize 0.45 linewidth 1.6 dashtype 1 linecolor rgb '#0072B2' title 'Near field'
set title '(d) Mx' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Mean drift (kN m/m²)'
set xrange [0.39:1.11]
set yrange [*:*]
set key off
plot 'rao/drift_mx_near.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 7 pointsize 0.45 linewidth 1.6 dashtype 1 linecolor rgb '#0072B2' title 'Near field'
set title '(e) My' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Mean drift (kN m/m²)'
set xrange [0.39:1.11]
set yrange [*:*]
set key off
plot 'rao/drift_my_near.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 7 pointsize 0.45 linewidth 1.6 dashtype 1 linecolor rgb '#0072B2' title 'Near field'
set title '(f) Mz' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Mean drift (kN m/m²)'
set xrange [0.39:1.11]
set yrange [*:*]
set key at screen 0.5,0.055 center horizontal maxrows 2 font 'Times New Roman,18.15' samplen 2.2
plot 'rao/drift_mz_near.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 7 pointsize 0.45 linewidth 1.6 dashtype 1 linecolor rgb '#0072B2' title 'Near field', \
'rao/drift_mz_far.rao' using (($1 >= 0.4 && $1 <= 1.1) ? $1 : 1/0):($2/1000) with linespoints pointtype 8 pointsize 0.45 linewidth 1.6 dashtype 2 linecolor rgb '#D55E00' title 'Far field'
unset multiplot
unset output
