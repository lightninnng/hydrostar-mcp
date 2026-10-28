reset
set terminal svg size 2400,1540 noenhanced font 'Times New Roman,23'
set output '../../../docs/assets/platform-second-order-qtf.svg'
set encoding utf8
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror
set grid back linewidth 0.5 linecolor rgb '#E0E5E9'
set format y '%.3g'
set key off
set multiplot layout 2,3 rowsfirst margins 0.08,0.98,0.20,0.84 spacing 0.085,0.18 title 'Semisubmersible: Full-potential difference-frequency QTF (60 deg, 200 m depth)' font 'Times New Roman,29.7'
set title '(a) Fx' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'QTF magnitude (kN/m²)'
set xrange [0.49:1.01]
set yrange [0:*]
set key off
plot 'rao/qtf_fx.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(2)**2+column(3)**2)/1000) with linespoints pointtype 7 pointsize 0.55 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Difference 0.00 rad/s', \
'rao/qtf_fx.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(4)**2+column(5)**2)/1000) with linespoints pointtype 8 pointsize 0.55 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Difference 0.05 rad/s', \
'rao/qtf_fx.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(6)**2+column(7)**2)/1000) with linespoints pointtype 9 pointsize 0.55 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title 'Difference 0.10 rad/s'
set title '(b) Fy' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'QTF magnitude (kN/m²)'
set xrange [0.49:1.01]
set yrange [0:*]
set key off
plot 'rao/qtf_fy.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(2)**2+column(3)**2)/1000) with linespoints pointtype 7 pointsize 0.55 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Difference 0.00 rad/s', \
'rao/qtf_fy.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(4)**2+column(5)**2)/1000) with linespoints pointtype 8 pointsize 0.55 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Difference 0.05 rad/s', \
'rao/qtf_fy.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(6)**2+column(7)**2)/1000) with linespoints pointtype 9 pointsize 0.55 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title 'Difference 0.10 rad/s'
set title '(c) Fz' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'QTF magnitude (kN/m²)'
set xrange [0.49:1.01]
set yrange [0:*]
set key off
plot 'rao/qtf_fz.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(2)**2+column(3)**2)/1000) with linespoints pointtype 7 pointsize 0.55 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Difference 0.00 rad/s', \
'rao/qtf_fz.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(4)**2+column(5)**2)/1000) with linespoints pointtype 8 pointsize 0.55 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Difference 0.05 rad/s', \
'rao/qtf_fz.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(6)**2+column(7)**2)/1000) with linespoints pointtype 9 pointsize 0.55 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title 'Difference 0.10 rad/s'
set title '(d) Mx' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'QTF magnitude (kN m/m²)'
set xrange [0.49:1.01]
set yrange [0:*]
set key off
plot 'rao/qtf_mx.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(2)**2+column(3)**2)/1000) with linespoints pointtype 7 pointsize 0.55 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Difference 0.00 rad/s', \
'rao/qtf_mx.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(4)**2+column(5)**2)/1000) with linespoints pointtype 8 pointsize 0.55 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Difference 0.05 rad/s', \
'rao/qtf_mx.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(6)**2+column(7)**2)/1000) with linespoints pointtype 9 pointsize 0.55 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title 'Difference 0.10 rad/s'
set title '(e) My' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'QTF magnitude (kN m/m²)'
set xrange [0.49:1.01]
set yrange [0:*]
set key off
plot 'rao/qtf_my.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(2)**2+column(3)**2)/1000) with linespoints pointtype 7 pointsize 0.55 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Difference 0.00 rad/s', \
'rao/qtf_my.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(4)**2+column(5)**2)/1000) with linespoints pointtype 8 pointsize 0.55 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Difference 0.05 rad/s', \
'rao/qtf_my.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(6)**2+column(7)**2)/1000) with linespoints pointtype 9 pointsize 0.55 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title 'Difference 0.10 rad/s'
set title '(f) Mz' font 'Times New Roman,23.1'
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'QTF magnitude (kN m/m²)'
set xrange [0.49:1.01]
set yrange [0:*]
set key at screen 0.5,0.055 center horizontal maxrows 2 font 'Times New Roman,18.15' samplen 2.2
plot 'rao/qtf_mz.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(2)**2+column(3)**2)/1000) with linespoints pointtype 7 pointsize 0.55 linewidth 1.7 dashtype 1 linecolor rgb '#0072B2' title 'Difference 0.00 rad/s', \
'rao/qtf_mz.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(4)**2+column(5)**2)/1000) with linespoints pointtype 8 pointsize 0.55 linewidth 1.7 dashtype 2 linecolor rgb '#D55E00' title 'Difference 0.05 rad/s', \
'rao/qtf_mz.qtf' using (($1 >= 0.5 && $1 <= 1.0) ? $1 : 1/0):(sqrt(column(6)**2+column(7)**2)/1000) with linespoints pointtype 9 pointsize 0.55 linewidth 1.7 dashtype 3 linecolor rgb '#009E73' title 'Difference 0.10 rad/s'
unset multiplot
unset output
