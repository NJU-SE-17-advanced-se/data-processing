import sys
import os
sys.path.insert(0, os.getcwd()) 
import unittest
from data_crawler.utils import remove_html

class test_db(unittest.TestCase):
    def test_remove_html(self):
        test_str = [
            {
                'str': 'C<span class="smallcaps smallerCapital">aramel</span>: detecting and fixing performance problems that have non-intrusive fixes',
                'exp':'Caramel: detecting and fixing performance problems that have non-intrusive fixes'
            },
            {
                'str':'Semantic differential repair for input validation and sanitization',
                'exp':'Semantic differential repair for input validation and sanitization'
            },
            {
                'str': 'D<inline-formula><tex-math notation=\"LaTeX\">$^2$</tex-math><alternatives><mml:math xmlns:mml=\"http://www.w3.org/1998/Math/MathML\"><mml:msup><mml:mrow/><mml:mn>2</mml:mn></mml:msup></mml:math><inline-graphic xlink:href=\"yang-ieq1-2867468.gif\" xmlns:xlink=\"http://www.w3.org/1999/xlink\"/></alternatives></inline-formula>HistoSketch: Discriminative and Dynamic Similarity-Preserving Sketching of Streaming Histograms',
                'exp': 'D$^2$HistoSketch: Discriminative and Dynamic Similarity-Preserving Sketching of Streaming Histograms'
            }
        ]

        for i in test_str:
            self.assertEqual(remove_html(i['str']), i['exp'])

if __name__ == '__main__':
    unittest.main()