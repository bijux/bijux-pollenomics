// Numerical investigation boundary: caller owns contiguous binary64 buffers.
#include <cmath>
#include <cstddef>
#include <vector>
#include <limits>

extern "C" int pollen_forward_batch(
    std::size_t rows, std::size_t rings, std::size_t taxa,
    const double* covers, const double* regional, const double* kernels,
    const double* fractions, const double* productivity, double* output) noexcept {
  if (!rows || !rings || !taxa || !covers || !regional || !kernels ||
      !fractions || !productivity || !output) return 1;
  if (rows > std::numeric_limits<std::size_t>::max() / taxa ||
      rings > std::numeric_limits<std::size_t>::max() / taxa) return 1;
  try {
    std::vector<double> factors(taxa, 0.0);
    for (std::size_t ring = 0; ring < rings; ++ring) {
      if (!std::isfinite(fractions[ring]) || fractions[ring] < 0.0 ||
          fractions[ring] > 1.0) return 1;
      for (std::size_t taxon = 0; taxon < taxa; ++taxon) {
        const double kernel = kernels[ring * taxa + taxon];
        if (!std::isfinite(kernel) || kernel < 0.0) return 1;
        factors[taxon] += fractions[ring] * kernel;
      }
    }
    for (std::size_t taxon = 0; taxon < taxa; ++taxon) {
      if (!std::isfinite(regional[taxon]) || regional[taxon] < 0.0 ||
          !std::isfinite(productivity[taxon]) || productivity[taxon] <= 0.0)
        return 1;
    }
    for (std::size_t row = 0; row < rows; ++row) {
      double closure = 0.0, mass = 0.0;
      for (std::size_t taxon = 0; taxon < taxa; ++taxon) {
        const std::size_t index = row * taxa + taxon;
        if (!std::isfinite(covers[index]) || covers[index] < 0.0) return 1;
        closure += covers[index];
        output[index] = factors[taxon] * covers[index] * productivity[taxon]
                        + regional[taxon];
        if (!std::isfinite(output[index]) || output[index] < 0.0) return 1;
        mass += output[index];
      }
      if (std::abs(closure - 1.0) > 1e-12 || !std::isfinite(mass) || mass <= 0.0)
        return 1;
      for (std::size_t taxon = 0; taxon < taxa; ++taxon)
        output[row * taxa + taxon] /= mass;
    }
  } catch (...) {
    // Exceptions never cross the private C call boundary.
    return 2;
  }
  return 0;
}
