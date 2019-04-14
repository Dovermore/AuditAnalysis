#!/usr/bin/env Rscript

# Draw plots of the certification probabilities and ROC curves for all methods
# for all audit runs.


# =============================================================================
# Parameter settings.

datadir <- file.path("..", "data")
outdir  <- file.path("..", "figures")

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
# Plotting functions.

# Plot the certification probabilities against threshold, for various true
# winning probabilities, for results for a given audit method.
certplot <- function(d, refline = TRUE, draw.legend = FALSE, ...) {
  plot(`0.5` ~ thresh, d, type = "o", pch = 20, ylim = c(0, 1),
       xlab = "Control parameter (alpha or posterior)",
       ylab = "Certification probability", ...)
  lines(`0.52` ~ thresh, d, type = "o", pch = 20, col = 2)
  lines(`0.58` ~ thresh, d, type = "o", pch = 20, col = 3)
  lines(`0.7`  ~ thresh, d, type = "o", pch = 20, col = 4)
  if (refline)
    abline(0, 1, lty = 2, col = "darkgrey")
  if (draw.legend)
    legend("topright", c("0.5 (null)", "0.52", "0.58", "0.7"),
           title = "True winning prop.", bg = "white",
           col = 1:4, lty = 1, pch = 20)
}

# Plot ROC curves for a given audit method, for various true winning
# probabilities.
rocplot <- function(d, refline = TRUE, draw.legend = FALSE, ...) {
  plot(`0.52` ~ `0.5`, d, type = "o", pch = 20, col = 2, ylim = c(0, 1),
       xlab = "Miscertification prob. (type 1 error)",
       ylab = "Correct certification prob. (power)", ...)
  lines(`0.58` ~ `0.5`, d, type = "o", pch = 20, col = 3)
  lines(`0.7`  ~ `0.5`, d, type = "o", pch = 20, col = 4)
  if (refline)
    abline(0, 1, lty = 2, col = "darkgrey")
  if (draw.legend)
    legend("bottomright", c("0.52", "0.58", "0.7"),
           title = "True winning prop.", bg = "white",
           col = 2:4, lty = 1, pch = 20)
}


# =============================================================================
# Functions for creating the title page.

interpret.audit.label <- function(audit.run.label) {
  total.ballots <- as.integer(substr(audit.run.label, 1,  6))
  max.sampsize  <- as.integer(substr(audit.run.label, 7, 10))
  replacement   <- ifelse(substr(audit.run.label, 12, 13) == "w",
                          "WITH", "WITHOUT")
  paste0("Total ballots = ",      total.ballots, "\n",
         "Maximum sample size = ", max.sampsize, "\n",
         "Sampling ", replacement, " replacement")
}

# Create a blank plot with a text message.
info <- function(message, cex = 2, font = 2, ...) {
  frame()
  text(0.5, 0.5, message, cex = cex, font = font, ...)
}


# =============================================================================
# Functions for creating the PDF output.

# Draw all of the method-specific plots and output in a PDF file.
writepdf <- function(audit.run, results.tables) {
  outfile <- paste0("certprob_", audit.run, ".pdf")
  outpath <- file.path(outdir, outfile)
  pdf(outpath, 9, 7)
  info(interpret.audit.label(audit.run))
  par(mfcol = c(2, 3))
  for (i in seq_along(results.tables)) {
    method    <- names(results.tables)[i]
    d         <- results.tables[[method]]
    heading   <- method.names[method]
    do.legend <- i %% 3 == 0

    certplot(d, main = heading, draw.legend = do.legend)
    rocplot( d,                 draw.legend = do.legend)
  }
  dev.off()
  invisible(NULL)
}


# =============================================================================
# Putting it all together.

process.audit <- function(audit.run) {
  message("Processing: ", audit.run)
  tables <- load.table.files(audit.run)
  writepdf(audit.run, tables)
  invisible(NULL)
}

process.audits <- function() {
  Map(process.audit, audit.runs)
  invisible(NULL)
}


# =============================================================================
# Do it!

process.audits()
