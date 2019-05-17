from datetime import datetime, timedelta
import sys

def getDates(granule):
    details = granule.split("_")
    date_fin = format_date(details[5][:8])
    date_deb1 = format_date(details[7][1:9])
    date_deb2 = format_date(details[8][:8])
    date_deb = min(date_deb1, date_deb2)

    if (date_deb == date_fin):
        date_fin = add_one_day(date_fin)

    return date_deb, date_fin


def format_date(date):
    """
    Convert "YYYYMMJJ" to "YYYY-MM-JJ"
        :param date: string date of format "YYYYMMJJ"
    """
    return datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")

def add_one_day(date):
    return datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)


def startProgress(title):
    global progress_x
    sys.stdout.write(title + ": [" + "-"*50 + "]" + chr(8)*51)
    sys.stdout.flush()
    progress_x = 0


def progress(x):
    global progress_x
    x = int(x * 50 // 100)
    sys.stdout.write("#" * (x - progress_x))
    sys.stdout.flush()
    progress_x = x


def endProgress():
    sys.stdout.write("#" * (50 - progress_x) + "]\n")
    sys.stdout.flush()


def unzipFile(source):
    """
    Arguments:
        :param source: file.gz name to uncompress  
    """
    import gzip

    input = gzip.GzipFile(source, 'rb')
    s = input.read()
    input.close()

    output = open(source[:-3], 'wb')
    output.write(s)
    output.close()

    print("Fichier enregistré !")
