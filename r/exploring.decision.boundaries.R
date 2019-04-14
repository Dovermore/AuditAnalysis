#!/usr/bin/env Rscript

# Draw plots of examples of decision boundaries for different audit methods.


# =============================================================================
# Parameter settings.

datadir <- file.path("..", "data")
outdir  <- file.path("..", "figures")

method.names <- c(
  clip      = "ClipAudit",
  naive     = "Naive",
  bayesC    = "BayesCont(1,1)",
  bayes500  = "Bayes500(1,1)",
  bayes200  = "Bayes200(1,1)",
  bayes0101 = "Bayes500(1,1)",
  bayes0104 = "Bayes500(1,4)",
  bayes0109 = "Bayes500(1,9)",
  bayes0401 = "Bayes500(4,1)",
  bayes0901 = "Bayes500(9,1)",
  bravo052  = "BRAVO(0.52)",
  bravo058  = "BRAVO(0.58)",
  bravo070  = "BRAVO(0.70)")


# =============================================================================
# Calculation of decision boundaries.
#
# These are the minimum number of observations (for a given sample size) to
# certify the election.

# Bayesian (discrete version, assumes sampling without replacement).
# n = sample size
# N = total ballots
# h = threshold on posterior
# a, b = parameters for the beta prior
bayes_disc_bound <- function(n = 20, N = 200, h = 0.1, a = 1, b = 1) {
  ys <- seq(0, n)  # possible observations
  ps <- extraDistr::pbbinom(0.5 * N - ys, N - n, a + ys, b + n - ys) # posterior probs of upset
  ycert <- which(ps < h)  # which observations lead to certification
  if (length(ycert) < 1)
    NA  # certification not possible
  else
    head(ycert, 1) - 1
}

# Bayesian (continuous version, assumes sampling with replacement).
# n = sample size
# h = threshold on posterior
# a, b = parameters for the beta prior
bayes_cont_bound <- function(n = 20, h = 0.1, a = 1, b = 1) {
  ys <- seq(0, n)  # possible observations
  ps <- pbeta(0.5, a + ys, b + n - ys)  # posterior probs of upset
  ycert <- which(ps < h)  # which observations lead to certification
  if (length(ycert) < 1)
    NA  # certification not possible
  else
    head(ycert, 1) - 1
}

# ClipAudit.
# n = sample size
# a = alpha parameter
clip_beta <- function(n, a) {  # approx. value of beta parameter
  0.075 * log(n) + 0.7 * qnorm(1 - a) + 0.86
}
clip_bound <- function(n = 20, a = 0.1) {
  0.5 * sqrt(n) * (clip_beta(n, a) + sqrt(n))
}

# Naive proportion HT-based audit.
# n = sample size
# a = significance level
naiveprop_bound <- function(n = 20, a = 0.1) {
  0.5 * sqrt(n) * (qnorm(1 - a) + sqrt(n))
}

# BRAVO.
# n = sample size
# pr = reported winning probability
# a = risk limit
bravo_bound <- function(n = 20, pr = 0.6, a = 0.1) {
  stopifnot(pr > 0.5)
  - (log(a) + n * log(2) + n * log(1 - pr)) / (log(pr) - log(1 - pr))
}


# =============================================================================
# Do it.

outfile <- "decision.boundary.examples.pdf"
outpath <- file.path(outdir, outfile)
pdf(outpath, 7, 7)


h <- 0.1  # threshold (used indirectly...)
nmax <- 200  # maximum sample size to explore
ns <- seq.int(nmax)


## Version 2.

bounds2 <- cbind(
  bayes0101 = Vectorize(bayes_disc_bound)(ns, N = 500, h = 0.01,   a = 1, b = 1),
  bayes0104 = Vectorize(bayes_disc_bound)(ns, N = 500, h = 0.031,  a = 1, b = 4),
  bayes0109 = Vectorize(bayes_disc_bound)(ns, N = 500, h = 0.075,  a = 1, b = 9),
  bayes0401 = Vectorize(bayes_disc_bound)(ns, N = 500, h = 0.0025, a = 4, b = 1),
  bayes0901 = Vectorize(bayes_disc_bound)(ns, N = 500, h = 0.0001, a = 9, b = 1),
  bravo070  = Vectorize(bravo_bound)(ns, 0.70, a = 0.13),
  bravo058  = Vectorize(bravo_bound)(ns, 0.58, a = 0.15),
  bravo052  = Vectorize(bravo_bound)(ns, 0.52, a = 0.15),
  clip      = Vectorize(clip_bound)( ns,       a = 0.14),
  naive     = Vectorize(naiveprop_bound)(ns,   a = 0.1)
)
boundsp2 <- bounds2 / ns  # counts -> sample proportions

ylim <- c(0.5, 1)
lty <- c(1, 2, 3, 2, 3, 1, 2, 4, 1, 3)
col <- c(3, 4, 4, 5, 5, 6, 6, 6, 1, 1)
lwd <- c(2, 1, 2, 1, 2, 2, 2, 2, 1, 1)

matplot(ns, boundsp2, type = "l", ylim = ylim, lty = lty, col = col, lwd = lwd,
        xlab = "Audit sample size", ylab = "Sample proportion",
        main = "Decision boundaries")
legend("topright", method.names[colnames(boundsp2)],
       lty = lty, col = col, lwd = lwd)


## Version 1.

bounds1 <- cbind(
  bayesC   = Vectorize(bayes_cont_bound)(ns,          h = 0.01),
  bayes500 = Vectorize(bayes_disc_bound)(ns, N = 500, h = 0.01),
  bayes200 = Vectorize(bayes_disc_bound)(ns, N = 200, h = 0.01),
  bravo070 = Vectorize(bravo_bound)(ns, 0.70, a = 0.13),
  bravo058 = Vectorize(bravo_bound)(ns, 0.58, a = 0.15),
  bravo052 = Vectorize(bravo_bound)(ns, 0.52, a = 0.15),
  clip     = Vectorize(clip_bound)( ns,       a = 0.14),
  naive    = Vectorize(naiveprop_bound)(ns,   a = 0.1)
)
boundsp1 <- bounds1 / ns  # counts -> sample proportions

ylim <- c(0.5, 1)
lty <- c(1, 1, 2, 1, 2, 4, 1, 3)
col <- c(3, 3, 3, 6, 6, 6, 1, 1)
lwd <- c(1, 2, 1, 2, 2, 2, 1, 1)

matplot(ns, boundsp1, type = "l", ylim = ylim, lty = lty, col = col, lwd = lwd,
        xlab = "Audit sample size", ylab = "Sample proportion",
        main = "Decision boundaries")
legend("topright", method.names[colnames(boundsp1)],
       lty = lty, col = col, lwd = lwd)


dev.off()
