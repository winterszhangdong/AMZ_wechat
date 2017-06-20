import logging

def test(a):
    print int(a)


def test2():
    try:
        test('aaaaa')
    except Exception as e:
        logging.exception(e)


# test('dfasfdf')
test2()