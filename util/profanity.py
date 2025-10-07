from profanityfilter import ProfanityFilter

pf = ProfanityFilter()


def profanity_check(name):

    if pf.is_clean(name):
        return name

    return pf.censor(name)
