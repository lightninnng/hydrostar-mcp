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
T=125.6637061435917
do for [f=0:N-1] {
t=f*T/N
set terminal svg size 1800,1152 noenhanced font 'Times New Roman,20'
set output sprintf('%s/map-%03d.svg',OUTDIR,f)
set label 900 'Heading 60 deg; depth 200 m; q(t) = Re[Q exp(i Delta t)]; coefficient gain 1x' at screen 0.5,0.93 center font 'Times New Roman,20'
set label 901 sprintf('Physical t = %.2f s; t/T = %.3f; T = %.3f s',t,t/T,T) at screen 0.5,0.885 center font 'Times New Roman,21'
set label 902 'Native HydroStar QTF / Gnuplot; Mz: convergence study' at screen 0.5,0.035 center font 'Times New Roman,19'
set multiplot layout 2,3 rowsfirst margins 0.07,0.90,0.19,0.82 spacing 0.10,0.21 title 'Difference-frequency QTF: phase-resolved coefficients' font 'Times New Roman,27'
set title '(a) Fx (kN/m²)'
unset arrow
unset grid
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Δω (rad/s)'
set xrange [0.475:1.125]
set yrange [-0.025:0.125]
set xtics (0.5,0.7,0.9,1.1)
set ytics (0,0.05,0.10)
set format cb '%.0f'
set cbrange [-31.291:31.291]
set cbtics (-31.291,0,31.291)
set colorbox vertical user origin 0.289000,0.610000 size 0.009,0.210000
plot 'rao/qtf_fx.qtf' using (($1>=0.499999 && $1<=1.100001) ? $1 : 1/0):(0):($1-0.025):($1+0.025):(-0.025):(0.025):((column(2)*cos(0*t)-column(3)*sin(0*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_fx.qtf' using (($1>=0.499999 && $1<=1.050001) ? $1 : 1/0):(0.05):($1-0.025):($1+0.025):(0.025):(0.075):((column(4)*cos(0.05*t)-column(5)*sin(0.05*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_fx.qtf' using (($1>=0.499999 && $1<=1.000001) ? $1 : 1/0):(0.1):($1-0.025):($1+0.025):(0.075):(0.125):((column(6)*cos(0.1*t)-column(7)*sin(0.1*t))/1000) with boxxyerrorbars fillcolor palette notitle
unset label 900
unset label 901
unset label 902
set title '(b) Fy (kN/m²)'
unset arrow
unset grid
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel ''
set xrange [0.475:1.125]
set yrange [-0.025:0.125]
set xtics (0.5,0.7,0.9,1.1)
set ytics (0,0.05,0.10)
set format cb '%.0f'
set cbrange [-54.217:54.217]
set cbtics (-54.217,0,54.217)
set colorbox vertical user origin 0.599000,0.610000 size 0.009,0.210000
plot 'rao/qtf_fy.qtf' using (($1>=0.499999 && $1<=1.100001) ? $1 : 1/0):(0):($1-0.025):($1+0.025):(-0.025):(0.025):((column(2)*cos(0*t)-column(3)*sin(0*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_fy.qtf' using (($1>=0.499999 && $1<=1.050001) ? $1 : 1/0):(0.05):($1-0.025):($1+0.025):(0.025):(0.075):((column(4)*cos(0.05*t)-column(5)*sin(0.05*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_fy.qtf' using (($1>=0.499999 && $1<=1.000001) ? $1 : 1/0):(0.1):($1-0.025):($1+0.025):(0.075):(0.125):((column(6)*cos(0.1*t)-column(7)*sin(0.1*t))/1000) with boxxyerrorbars fillcolor palette notitle
set title '(c) Fz (kN/m²)'
unset arrow
unset grid
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel ''
set xrange [0.475:1.125]
set yrange [-0.025:0.125]
set xtics (0.5,0.7,0.9,1.1)
set ytics (0,0.05,0.10)
set format cb '%.0f'
set cbrange [-35.673:35.673]
set cbtics (-35.673,0,35.673)
set colorbox vertical user origin 0.909000,0.610000 size 0.009,0.210000
plot 'rao/qtf_fz.qtf' using (($1>=0.499999 && $1<=1.100001) ? $1 : 1/0):(0):($1-0.025):($1+0.025):(-0.025):(0.025):((column(2)*cos(0*t)-column(3)*sin(0*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_fz.qtf' using (($1>=0.499999 && $1<=1.050001) ? $1 : 1/0):(0.05):($1-0.025):($1+0.025):(0.025):(0.075):((column(4)*cos(0.05*t)-column(5)*sin(0.05*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_fz.qtf' using (($1>=0.499999 && $1<=1.000001) ? $1 : 1/0):(0.1):($1-0.025):($1+0.025):(0.075):(0.125):((column(6)*cos(0.1*t)-column(7)*sin(0.1*t))/1000) with boxxyerrorbars fillcolor palette notitle
set title '(d) Mx (kN m/m²)'
unset arrow
unset grid
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel 'Δω (rad/s)'
set xrange [0.475:1.125]
set yrange [-0.025:0.125]
set xtics (0.5,0.7,0.9,1.1)
set ytics (0,0.05,0.10)
set format cb '%.0f'
set cbrange [-768.34:768.34]
set cbtics (-768.34,0,768.34)
set colorbox vertical user origin 0.289000,0.190000 size 0.009,0.210000
plot 'rao/qtf_mx.qtf' using (($1>=0.499999 && $1<=1.100001) ? $1 : 1/0):(0):($1-0.025):($1+0.025):(-0.025):(0.025):((column(2)*cos(0*t)-column(3)*sin(0*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_mx.qtf' using (($1>=0.499999 && $1<=1.050001) ? $1 : 1/0):(0.05):($1-0.025):($1+0.025):(0.025):(0.075):((column(4)*cos(0.05*t)-column(5)*sin(0.05*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_mx.qtf' using (($1>=0.499999 && $1<=1.000001) ? $1 : 1/0):(0.1):($1-0.025):($1+0.025):(0.075):(0.125):((column(6)*cos(0.1*t)-column(7)*sin(0.1*t))/1000) with boxxyerrorbars fillcolor palette notitle
set title '(e) My (kN m/m²)'
unset arrow
unset grid
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel ''
set xrange [0.475:1.125]
set yrange [-0.025:0.125]
set xtics (0.5,0.7,0.9,1.1)
set ytics (0,0.05,0.10)
set format cb '%.0f'
set cbrange [-444.69:444.69]
set cbtics (-444.69,0,444.69)
set colorbox vertical user origin 0.599000,0.190000 size 0.009,0.210000
plot 'rao/qtf_my.qtf' using (($1>=0.499999 && $1<=1.100001) ? $1 : 1/0):(0):($1-0.025):($1+0.025):(-0.025):(0.025):((column(2)*cos(0*t)-column(3)*sin(0*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_my.qtf' using (($1>=0.499999 && $1<=1.050001) ? $1 : 1/0):(0.05):($1-0.025):($1+0.025):(0.025):(0.075):((column(4)*cos(0.05*t)-column(5)*sin(0.05*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_my.qtf' using (($1>=0.499999 && $1<=1.000001) ? $1 : 1/0):(0.1):($1-0.025):($1+0.025):(0.075):(0.125):((column(6)*cos(0.1*t)-column(7)*sin(0.1*t))/1000) with boxxyerrorbars fillcolor palette notitle
set title '(f) Mz (research) (kN m/m²)'
unset arrow
unset grid
set xlabel 'Wave frequency ω1 (rad/s)'
set ylabel ''
set xrange [0.475:1.125]
set yrange [-0.025:0.125]
set xtics (0.5,0.7,0.9,1.1)
set ytics (0,0.05,0.10)
set format cb '%.1f'
set cbrange [-3.62069460144:3.62069460144]
set cbtics (-3.62069460144,0,3.62069460144)
set colorbox vertical user origin 0.909000,0.190000 size 0.009,0.210000
plot 'rao/qtf_mz.qtf' using (($1>=0.499999 && $1<=1.100001) ? $1 : 1/0):(0):($1-0.025):($1+0.025):(-0.025):(0.025):((column(2)*cos(0*t)-column(3)*sin(0*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_mz.qtf' using (($1>=0.499999 && $1<=1.050001) ? $1 : 1/0):(0.05):($1-0.025):($1+0.025):(0.025):(0.075):((column(4)*cos(0.05*t)-column(5)*sin(0.05*t))/1000) with boxxyerrorbars fillcolor palette notitle, \
'rao/qtf_mz.qtf' using (($1>=0.499999 && $1<=1.000001) ? $1 : 1/0):(0.1):($1-0.025):($1+0.025):(0.075):(0.125):((column(6)*cos(0.1*t)-column(7)*sin(0.1*t))/1000) with boxxyerrorbars fillcolor palette notitle
unset multiplot
unset output
unset label 900
unset label 901
unset label 902
}
