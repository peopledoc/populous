import random

import jinja2


jinja_env = jinja2.Environment()
jinja_env.undefined = jinja2.StrictUndefined


# Fix an issue where 'random' filter is being inlined, resulting in the
# same value being generated every time.
# cf https://github.com/pallets/jinja/pull/478

@jinja2.contextfilter
def do_random(context, seq):
    """Return a random item from the sequence."""
    try:
        return random.choice(seq)
    except IndexError:
        return context.environment.undefined(
            'No random item, sequence was empty.'
        )


jinja_env.filters['random'] = do_random
