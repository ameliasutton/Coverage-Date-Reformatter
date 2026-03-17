pip install -r requirements.txt
pause
pyinstaller --onefile --windowed dateReformatting.py -n dateReformatting --distpath "%cd%" --workpath exe_build --noconfirm
del dateReformatting.spec
rmdir /Q /S exe_build
pause