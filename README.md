# Grab PLOS
Save the articles of a PLOS journal in .txt files

## Usage

    $ grab_plos.py --help
    usage: grab_plos.py [-h] --journal-url URL --save-to FOLDER [--threads N]
                        [--log LOG]
    
    Save the articles of a PLOS journal in .txt files

    required arguments:
      --journal-url URL  the archive page of the journal; 
                         example: http://www.ploscompbiol.org/article/browse/volume
      --save-to FOLDER   the destination folder
    
    optional arguments:
      -h, --help         show this help message and exit
      --threads N        the number of threads for downloading (default: 10)
      --log LOG          the log file (default: a log file with the name generated from the current time)
