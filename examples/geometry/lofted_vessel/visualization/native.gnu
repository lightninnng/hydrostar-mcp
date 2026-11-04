set terminal windows
set grid
set title 'surge.rao'
set xlabel ' Frequency (rad/s) '
set ylabel 'Surge motion  (m/m)'
plot \
'rao/surge.rao' u 1:  2 t '  0.00'     w lp ,\
'rao/surge.rao' u 1:  3 t ' 60.00'     w lp ,\
'rao/surge.rao' u 1:  4 t '120.00'     w lp ,\
'rao/surge.rao' u 1:  5 t '180.00'     w lp
pause -1
set terminal windows
set grid
set title 'sway.rao'
set xlabel ' Frequency (rad/s) '
set ylabel 'Sway motion  (m/m)'
plot \
'rao/sway.rao' u 1:  2 t '  0.00'     w lp ,\
'rao/sway.rao' u 1:  3 t ' 60.00'     w lp ,\
'rao/sway.rao' u 1:  4 t '120.00'     w lp ,\
'rao/sway.rao' u 1:  5 t '180.00'     w lp
pause -1
set terminal windows
set grid
set title 'heave.rao'
set xlabel ' Frequency (rad/s) '
set ylabel 'Heave motion  (m/m)'
plot \
'rao/heave.rao' u 1:  2 t '  0.00'     w lp ,\
'rao/heave.rao' u 1:  3 t ' 60.00'     w lp ,\
'rao/heave.rao' u 1:  4 t '120.00'     w lp ,\
'rao/heave.rao' u 1:  5 t '180.00'     w lp
pause -1
set terminal windows
set grid
set title 'roll.rao'
set xlabel ' Frequency (rad/s) '
set ylabel 'Roll motion  (deg/m)'
plot \
'rao/roll.rao' u 1:  2 t '  0.00'     w lp ,\
'rao/roll.rao' u 1:  3 t ' 60.00'     w lp ,\
'rao/roll.rao' u 1:  4 t '120.00'     w lp ,\
'rao/roll.rao' u 1:  5 t '180.00'     w lp
pause -1
set terminal windows
set grid
set title 'pitch.rao'
set xlabel ' Frequency (rad/s) '
set ylabel 'Pitch motion  (deg/m)'
plot \
'rao/pitch.rao' u 1:  2 t '  0.00'     w lp ,\
'rao/pitch.rao' u 1:  3 t ' 60.00'     w lp ,\
'rao/pitch.rao' u 1:  4 t '120.00'     w lp ,\
'rao/pitch.rao' u 1:  5 t '180.00'     w lp
pause -1
set terminal windows
set grid
set title 'yaw.rao'
set xlabel ' Frequency (rad/s) '
set ylabel 'Yaw motion  (deg/m)'
plot \
'rao/yaw.rao' u 1:  2 t '  0.00'     w lp ,\
'rao/yaw.rao' u 1:  3 t ' 60.00'     w lp ,\
'rao/yaw.rao' u 1:  4 t '120.00'     w lp ,\
'rao/yaw.rao' u 1:  5 t '180.00'     w lp
pause -1
