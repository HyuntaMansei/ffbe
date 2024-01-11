set root=C:\Users\jchoi
call %root%\anaconda3\Scripts\activate.bat %root%\anaconda3
call conda activate py311
call cd %root%\Coding\python\ffbe
call python ffbe_gui.py 3400 500 E0D

pause