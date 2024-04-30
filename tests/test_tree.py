from mavlink_analyzer.main import Analyzer

def test_tree1():
    app = Analyzer()
    tree = {
        1: {
            1: {
                'HB': 5,
                "ALERT": 1
            }
        }
    }
    app.buile_tree(tree)
    assert True