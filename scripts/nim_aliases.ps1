# NIM batch aliases - source with: . D:\software\scripts\nim_aliases.ps1
# Or add to $PROFILE for persistent use

$NimBatch = "D:\software\scripts\nim_batch.py"
$Python = "python"

function nim-explain { & $Python $NimBatch "explain this code" $args }
function nim-docs    { & $Python $NimBatch "add docstrings" $args --model mistralai/codestral-22b-instruct-v0.1 }
function nim-summary { & $Python $NimBatch "summarize" $args }
