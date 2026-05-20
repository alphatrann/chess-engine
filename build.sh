python -m nuitka \
  --standalone \
  --follow-imports \
  --include-data-dir=resources=resources \
  --output-dir=. \
  --output-filename=engine \
  src/server.py