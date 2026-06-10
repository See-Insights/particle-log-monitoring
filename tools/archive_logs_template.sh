#!/bin/bash

DAY=$(date -v-1d +%Y%m%d)

for DIR in \
"$HOME/ParticleLogs/products/PRODUCT-ALPHA" \
"$HOME/ParticleLogs/products/PRODUCT-BETA" \
"$HOME/ParticleLogs/products/PRODUCT-GAMMA"
do
    if [ -f "$DIR/latest.raw.log" ]; then
        mkdir -p "$DIR/archive"

        cp "$DIR/latest.raw.log" \
           "$DIR/archive/product-events-${DAY}.raw.log"

        gzip -f "$DIR/archive/product-events-${DAY}.raw.log"

        echo "Archived: $(basename "$DIR")"
    else
        echo "Skipped: $(basename "$DIR") (no latest.raw.log)"
    fi
done

echo "Done: ${DAY}"
