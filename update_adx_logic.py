"""
Script to update fno_trading_bot.py to disable 15m ADX check
"""

import re

# Read the file
with open('src/fno_trading_bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Comment out 15m ADX check for CE (around line 230-234)
pattern1 = r"(\s+# Condition 8: 15m ADX > 25\s+adx = current_row\['ADX'\]\s+if adx <= self\.config\.adx_min:\s+logger\.info\(f\"{underlying} \[CE\]: ADX Check Failed.*?\"\)\s+return False)"
replacement1 = r"""
    # Condition 8: 15m ADX > 25 (OPTIONAL - CURRENTLY DISABLED)
    # adx = current_row['ADX']
    # if adx <= self.config.adx_min:
    #     logger.info(f"{underlying} [CE]: ADX Check Failed (Value: {adx:.2f} | Min: {self.config.adx_min})")
    #     return False"""

content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

# Pattern 2: Update Daily ADX comment for CE
content = content.replace("# Condition 9: Daily ADX > 20", "# Condition 9: Daily ADX > 25", 1)

# Pattern 3: Remove 15m ADX from CE success log
pattern3 = r'logger\.info\(f"OK {underlying}: All CE entry conditions met \| RSI={rsi:.2f} \| 15m ADX={adx:.2f} \| Daily ADX={daily_adx:.2f} \| VIX={vix:.2f}"\)'
replacement3 = r'logger.info(f"OK {underlying}: All CE entry conditions met | RSI={rsi:.2f} | Daily ADX={daily_adx:.2f} | VIX={vix:.2f}")'
content = re.sub(pattern3, replacement3, content)

# Pattern 4: Comment out 15m ADX check for PE (around line 353-357)
pattern4 = r"(\s+# Condition 8: 15m ADX > 25\s+adx = current_row\['ADX'\]\s+if adx <= self\.config\.adx_min:\s+logger\.info\(f\"{underlying} \[PE\]: ADX Check Failed.*?\"\)\s+return False)"
replacement4 = r"""
    # Condition 8: 15m ADX > 25 (OPTIONAL - CURRENTLY DISABLED)
    # adx = current_row['ADX']
    # if adx <= self.config.adx_min:
    #     logger.info(f"{underlying} [PE]: ADX Check Failed (Value: {adx:.2f} | Min: {self.config.adx_min})")
    #     return False"""

# Find the second occurrence (PE section)
matches = list(re.finditer(pattern4, content, flags=re.DOTALL))
if len(matches) >= 1:
    # Replace from the end to preserve positions
    for match in reversed(matches):
        content = content[:match.start()] + replacement4 + content[match.end():]

# Pattern 5: Update Daily ADX comment for PE (second occurrence)
parts = content.split("# Condition 9: Daily ADX > 20")
if len(parts) >= 3:
    content = parts[0] + "# Condition 9: Daily ADX > 25" + parts[1] + "# Condition 9: Daily ADX > 25" + "".join(parts[2:])

# Pattern 6: Remove 15m ADX from PE success log
pattern6 = r'logger\.info\(f"OK {underlying}: All PE entry conditions met \| RSI={rsi:.2f} \| 15m ADX={adx:.2f} \| Daily ADX={daily_adx:.2f} \| VIX={vix:.2f}"\)'
replacement6 = r'logger.info(f"OK {underlying}: All PE entry conditions met | RSI={rsi:.2f} | Daily ADX={daily_adx:.2f} | VIX={vix:.2f}")'
content = re.sub(pattern6, replacement6, content)

# Write back
with open('src/fno_trading_bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated fno_trading_bot.py:")
print("  - Disabled 15m ADX check for CE and PE")
print("  - Updated Daily ADX comments to >25")
print("  - Removed 15m ADX from success logs")
