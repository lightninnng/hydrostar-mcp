reset
set encoding utf8
if (!exists('OUTDIR')) OUTDIR='frames'
set border linewidth 0.8 linecolor rgb '#34424E'
set tics out nomirror
set format y '%.2g'
set format cb '%.2g'
set key off
set style fill solid 1.0 border rgb '#dce3e7'
set palette defined (-1 '#2166ac',0 '#f7f7f7',1 '#b2182b')
N=80
T=62.83185307179586
do for [f=0:N-1] {
t=f*T/N
set terminal svg size 1800,1152 noenhanced font 'Times New Roman,20'
set output sprintf('%s/harmonics-%03d.svg',OUTDIR,f)
set label 900 'ω1 = 0.80, ω2 = 0.90, Δω = 0.10 rad/s; heading 60 deg; depth 200 m; gain 1x' at screen 0.5,0.93 center font 'Times New Roman,20'
set label 901 sprintf('Physical t = %.2f s; t/T = %.3f; T = %.3f s',t,t/T,T) at screen 0.5,0.885 center font 'Times New Roman,21'
set label 902 'Native HydroStar QTF / Gnuplot; Mz: convergence study' at screen 0.5,0.035 center font 'Times New Roman,19'
set multiplot layout 2,3 rowsfirst margins 0.07,0.90,0.19,0.82 spacing 0.10,0.21 title 'Selected-pair QTF: normalized load harmonics' font 'Times New Roman,27'
set title '(a) Fx (kN/m²)'
unset arrow
unset colorbox
set grid back linewidth 0.5 linecolor rgb '#e0e5e9'
set xlabel 'Physical time (s)'
set ylabel 'Harmonic coefficient'
set xrange [-1.25663706:64.0884901]
set yrange [-30.2000456143:30.2000456143]
set xtics autofreq
set ytics autofreq
set samples 401
h(x)=(23132*cos(0.1*x)-11946*sin(0.1*x))/1000
set arrow 1 from t,-30.2000456143 to t,30.2000456143 nohead dashtype 2 linewidth 1 linecolor rgb '#9baab3'
plot h(x) with lines linewidth 1.2 linecolor rgb '#9baab3' notitle, (x<=t ? h(x) : 1/0) with lines linewidth 2 linecolor rgb '#0072b2' notitle, '+' using (t):(h(t)) every ::0::0 with points pointtype 7 pointsize 1.1 linecolor rgb '#d55e00' notitle
unset label 900
unset label 901
unset label 902
set title '(b) Fy (kN/m²)'
unset arrow
unset colorbox
set grid back linewidth 0.5 linecolor rgb '#e0e5e9'
set xlabel 'Physical time (s)'
set ylabel 'Harmonic coefficient'
set xrange [-1.25663706:64.0884901]
set yrange [-52.3286693697:52.3286693697]
set xtics autofreq
set ytics autofreq
set samples 401
h(x)=(40074*cos(0.1*x)-20714*sin(0.1*x))/1000
set arrow 1 from t,-52.3286693697 to t,52.3286693697 nohead dashtype 2 linewidth 1 linecolor rgb '#9baab3'
plot h(x) with lines linewidth 1.2 linecolor rgb '#9baab3' notitle, (x<=t ? h(x) : 1/0) with lines linewidth 2 linecolor rgb '#0072b2' notitle, '+' using (t):(h(t)) every ::0::0 with points pointtype 7 pointsize 1.1 linecolor rgb '#d55e00' notitle
set title '(c) Fz (kN/m²)'
unset arrow
unset colorbox
set grid back linewidth 0.5 linecolor rgb '#e0e5e9'
set xlabel 'Physical time (s)'
set ylabel 'Harmonic coefficient'
set xrange [-1.25663706:64.0884901]
set yrange [-38.9325168338:38.9325168338]
set xtics autofreq
set ytics autofreq
set samples 401
h(x)=(33154*cos(0.1*x)-5220.6*sin(0.1*x))/1000
set arrow 1 from t,-38.9325168338 to t,38.9325168338 nohead dashtype 2 linewidth 1 linecolor rgb '#9baab3'
plot h(x) with lines linewidth 1.2 linecolor rgb '#9baab3' notitle, (x<=t ? h(x) : 1/0) with lines linewidth 2 linecolor rgb '#0072b2' notitle, '+' using (t):(h(t)) every ::0::0 with points pointtype 7 pointsize 1.1 linecolor rgb '#d55e00' notitle
set title '(d) Mx (kN m/m²)'
unset arrow
unset colorbox
set grid back linewidth 0.5 linecolor rgb '#e0e5e9'
set xlabel 'Physical time (s)'
set ylabel 'Harmonic coefficient'
set xrange [-1.25663706:64.0884901]
set yrange [-580.765409663:580.765409663]
set xtics autofreq
set ytics autofreq
set samples 401
h(x)=(-426830*cos(0.1*x)-261680*sin(0.1*x))/1000
set arrow 1 from t,-580.765409663 to t,580.765409663 nohead dashtype 2 linewidth 1 linecolor rgb '#9baab3'
plot h(x) with lines linewidth 1.2 linecolor rgb '#9baab3' notitle, (x<=t ? h(x) : 1/0) with lines linewidth 2 linecolor rgb '#0072b2' notitle, '+' using (t):(h(t)) every ::0::0 with points pointtype 7 pointsize 1.1 linecolor rgb '#d55e00' notitle
set title '(e) My (kN m/m²)'
unset arrow
unset colorbox
set grid back linewidth 0.5 linecolor rgb '#e0e5e9'
set xlabel 'Physical time (s)'
set ylabel 'Harmonic coefficient'
set xrange [-1.25663706:64.0884901]
set yrange [-335.545569706:335.545569706]
set xtics autofreq
set ytics autofreq
set samples 401
h(x)=(246570*cos(0.1*x)--151250*sin(0.1*x))/1000
set arrow 1 from t,-335.545569706 to t,335.545569706 nohead dashtype 2 linewidth 1 linecolor rgb '#9baab3'
plot h(x) with lines linewidth 1.2 linecolor rgb '#9baab3' notitle, (x<=t ? h(x) : 1/0) with lines linewidth 2 linecolor rgb '#0072b2' notitle, '+' using (t):(h(t)) every ::0::0 with points pointtype 7 pointsize 1.1 linecolor rgb '#d55e00' notitle
set title '(f) Mz (research) (kN m/m²)'
unset arrow
unset colorbox
set grid back linewidth 0.5 linecolor rgb '#e0e5e9'
set xlabel 'Physical time (s)'
set ylabel 'Harmonic coefficient'
set xrange [-1.25663706:64.0884901]
set yrange [-2.07323818416:2.07323818416]
set xtics autofreq
set ytics autofreq
set samples 401
h(x)=(-810.96*cos(0.1*x)--1592.7*sin(0.1*x))/1000
set arrow 1 from t,-2.07323818416 to t,2.07323818416 nohead dashtype 2 linewidth 1 linecolor rgb '#9baab3'
plot h(x) with lines linewidth 1.2 linecolor rgb '#9baab3' notitle, (x<=t ? h(x) : 1/0) with lines linewidth 2 linecolor rgb '#0072b2' notitle, '+' using (t):(h(t)) every ::0::0 with points pointtype 7 pointsize 1.1 linecolor rgb '#d55e00' notitle
unset multiplot
unset output
unset label 900
unset label 901
unset label 902
}
