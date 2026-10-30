// Fixed-state observation of the original no-hiatus likelihood age function.
// Upstream files are supplied from the authenticated source archive at build time.
#include <Rcpp.h>
#include <array>
#include <cmath>
#include <vector>

#include "Matrix.cpp"
#include "gauss.cpp"
#include "ranfun.cpp"
#include "bacon.h"

// [[Rcpp::plugins(cpp11)]]

// [[Rcpp::export]]
Rcpp::List bacon_likelihood_ages(
    Rcpp::NumericMatrix states, Rcpp::NumericVector depths,
    double top_depth, double thick, double youngest_age, double oldest_age) {
  const int sections = states.ncol() - 2;
  if (sections < 2 || sections > 64 || states.nrow() < 1 ||
      states.nrow() > 32 || depths.size() < 1 || depths.size() > 256 ||
      !std::isfinite(top_depth) || !std::isfinite(thick) || thick <= 0 ||
      !std::isfinite(youngest_age) || !std::isfinite(oldest_age) ||
      youngest_age >= oldest_age) {
    Rcpp::stop("Invalid bounded no-hiatus oracle axes or geometry");
  }
  const double bottom_depth = top_depth + sections * thick;
  for (double depth : depths) {
    if (!std::isfinite(depth) || depth < top_depth || depth > bottom_depth) {
      Rcpp::stop("Oracle depth is outside the declared source model");
    }
  }
  for (double value : states) {
    if (!std::isfinite(value)) {
      Rcpp::stop("Oracle states must be finite serialized numbers");
    }
  }

  // Calendar-only fixture controls exercise the source class without curves
  // or a model fit. The class owns its determination collection.
  ConstCal calendar;
  Dets *dates = new Dets(2);
  char top_label[] = "calendar_top";
  char bottom_label[] = "calendar_bottom";
  dates->AddDet(new Det(top_label, 0, 30, top_depth, 0, 0, 3, 4, &calendar));
  dates->AddDet(new Det(bottom_label, 1000, 30, bottom_depth, 0, 0, 3, 4, &calendar));
  std::array<double, 1> hiatus = {{0}};
  std::array<double, 1> shape = {{1.5}};
  std::array<double, 1> rate = {{1.5 / 34.63225806451613}};
  std::array<double, 1> hiatus_shape = {{0.5}};
  std::array<double, 1> hiatus_rate = {{0.0005}};
  std::array<double *, 5> parameters = {{
      hiatus.data(), shape.data(), rate.data(),
      hiatus_shape.data(), hiatus_rate.data()}};
  BaconFix model(dates, sections, 0, parameters.data(), 6, 14,
                 youngest_age, oldest_age, 0, 10, top_depth,
                 bottom_depth, 1, 173173UL);

  Rcpp::LogicalVector support(states.nrow());
  Rcpp::LogicalVector finite_energy(states.nrow());
  Rcpp::NumericVector energy(states.nrow(), NA_REAL);
  Rcpp::NumericMatrix ages(states.nrow(), depths.size());
  std::fill(ages.begin(), ages.end(), NA_REAL);
  std::vector<double> state(states.ncol());
  for (int row = 0; row < states.nrow(); ++row) {
    for (int column = 0; column < states.ncol(); ++column) {
      state[column] = states(row, column);
    }
    support[row] = model.insupport(state.data()) != 0;
    if (!support[row]) {
      continue;
    }
    energy[row] = model.eval(state.data(), 0);
    finite_energy[row] = std::isfinite(energy[row]);
    if (!finite_energy[row]) {
      continue;
    }
    for (R_xlen_t column = 0; column < depths.size(); ++column) {
      // The two-argument source overload gives theta[K] at the last elbow:
      // its residual length is exactly zero. This avoids the one-argument
      // overload's read of theta[K+1] at that terminal model edge.
      ages(row, column) = depths[column] == model.GetcK()
          ? model.G(depths[column], state.data())
          : model.G(depths[column]);
    }
  }
  return Rcpp::List::create(
      Rcpp::Named("source_support") = support,
      Rcpp::Named("finite_energy") = finite_energy,
      Rcpp::Named("source_energy") = energy,
      Rcpp::Named("ages") = ages,
      Rcpp::Named("native_top_depth") = model.Getc0(),
      Rcpp::Named("native_model_end") = model.GetcK(),
      Rcpp::Named("native_section_width") =
          (model.GetcK() - model.Getc0()) / sections);
}
