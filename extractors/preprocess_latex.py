import json
import re
from pathlib import Path

def load_latex_rules(latex_json_path):
    with open(latex_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_latex(text, rules):
    # 依次应用每一类规则
    for group in rules.values():
        for pat, rep in group.items():
            text = re.sub(pat, rep, text)
    return text

# 示例用法
if __name__ == '__main__':
    raw_latex = r"\frac{a}{b} + \mathit{n} \leq \infty"
    rules = load_latex_rules("../data/latex_replacements.json")
    print(clean_latex(raw_latex, rules))
