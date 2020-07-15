def print_time(time_obj):
    seconds = time_obj.total_seconds()
    days = time_obj.days
    if days < 1:
        if seconds // 60 < 1:  # less than a minute
            return f'{int(seconds)} secs'
        elif seconds // 3600 < 1:  # less than an hour
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f'{mins} min{"s" if mins > 1 else ""} {str(secs) + " sec" if secs else ""}{"s" if secs > 1 else ""}'
        else:  # less than a day
            hrs = int(seconds // 3600)
            mins = int(seconds % 3600 // 60)
            return f'{hrs} hr{"s" if hrs > 1 else ""} {str(mins) + " min" if mins else ""}{"s" if mins > 1 else ""}'
    else:
        return f' {int(days)} day' + f'{"s" if days > 1 else ""}'