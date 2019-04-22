#!/usr/bin/env Rscript

# Determine settings for the control parameters (risk limits / posterior
# thresholds) to achieve a given type 1 error rate.


# =============================================================================
# Parameter settings.

datadir <- file.path("..", "data")
outdir  <- datadir

audit.runs <- c("0100000500_w",
                "0100000500_wo",
                "0005000200_w",
                "0005000200_wo")

files.to.load <- c(
  clip      = "clip_table.csv",
  bayes0101 = "bayesian0101_table.csv",
  bayes0104 = "bayesian0104_table.csv",
  bayes0109 = "bayesian0109_table.csv",
  bayes0401 = "bayesian0401_table.csv",
  bayes0901 = "bayesian0901_table.csv",
  bravo052p = "bravo052_power.csv",
  bravo058p = "bravo058_power.csv",
  bravo070p = "bravo070_power.csv",
  bravo052f = "bravo052_type1.csv",
  bravo058f = "bravo058_type1.csv",
  bravo070f = "bravo070_type1.csv")

bravo.methods <- c("bravo052", "bravo058", "bravo070")

method.names <- c(
  clip      = "ClipAudit",
  bayes0101 = "Bayes(1,1)",
  bayes0104 = "Bayes(1,4)",
  bayes0109 = "Bayes(1,9)",
  bayes0401 = "Bayes(4,1)",
  bayes0901 = "Bayes(9,1)",
  bravo052  = "BRAVO(0.52)",
  bravo058  = "BRAVO(0.58)",
  bravo070  = "BRAVO(0.70)")


# =============================================================================
# Functions for loading and munging data.

# Loads a single 'table' file.
loadtable <- function(f, check.names = FALSE, adjust.column1 = TRUE, ...) {
  d <- read.csv(f, check.names = check.names, ...)
  if (adjust.column1)
    colnames(d)[1] <- "thresh"
  invisible(d)
}

# Construct full relative paths for a single audit run.
full.paths <- function(audit.run) {
  indir <- file.path(datadir, audit.run)
  paths.to.load <- file.path(indir, files.to.load)
  names(paths.to.load) <- names(files.to.load)
  return(paths.to.load)
}

# Load all 'table' files.
load.table.files <- function(audit.run, munge = TRUE) {
  tables1 <- Map(loadtable, full.paths(audit.run))

  if (munge) {  # munge into standard format
    # Bayesian results: use upset probability rather than winner probability.
    for (i in grep("bayes", names(files.to.load))) {
      tables1[[i]]$thresh <- 1 - tables1[[i]]$thresh
    }

    # BRAVO: combine into single table.
    for (bm in bravo.methods) {
      bmp <- paste0(bm, "p")  # power results (label)
      bmf <- paste0(bm, "f")  # false positive results (label)
      tables1[[bm]] <- cbind(tables1[[bmp]], "0.5" = tables1[[bmf]][, 2])
    }

    # Take just the tables in standard format.
    tables <- tables1[c(1:6, 13:15)]
  } else {  # no munging, keep in raw format
    tables <- tables1
  }

  invisible(tables)
}


# =============================================================================
# Deterimining thresholds.

# Given a table of results, find the threshold that best achieves a given false
# positive rate.
best.thresh <- function(d, alpha = 0.1) {
  belowAlpha <- d[["0.5"]] < alpha
  goodThresh <- d[["thresh"]][belowAlpha]
  bestThresh <- max(goodThresh)
  return(bestThresh)
}


# =============================================================================
# Putting it all together.

process.audit <- function(audit.run) {
  message("Processing: ", audit.run)
  tables <- load.table.files(audit.run)
  sapply(tables, best.thresh)
}

process.audits <- function() {
  sapply(audit.runs, process.audit)
}


# =============================================================================
# Do it!

res <- process.audits()

outfile <- file.path(outdir, "calibrated.thresholds.csv")
write.csv(res, outfile)

cat("\n")
cat("Calibrated thresholds (written to CSV file):\n")
print(res)
