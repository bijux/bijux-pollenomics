# Preserve complete runtime observations before validating unchanged numerical replay custody.
guarded_replay <- function(original, destination, r_home, library, native_files, metadata_only = FALSE) {
  normalize <- function(path) normalizePath(path, winslash = "/", mustWork = TRUE)
  roots <- c(normalize(r_home), normalize(library))
  owned <- function(path) any(vapply(roots, function(root) identical(path, root) || startsWith(path, paste0(root, "/")), logical(1)))
  observed_path <- function(path) {
    problem <- NULL
    value <- tryCatch(normalize(path), error = function(e) { problem <<- conditionMessage(e); NULL })
    list(path = value, path_error = problem)
  }
  snapshot <- function() {
    info <- capture.output(sessionInfo())
    namespaces <- lapply(sort(loadedNamespaces()), function(name) {
      # Base owns no getNamespaceInfo path slot.
      raw <- if (identical(name, "base")) file.path(R.home("library"), "base") else getNamespaceInfo(name, "path")
      observed <- observed_path(raw)
      version <- if (identical(name, "base")) as.character(getRversion()) else as.character(getNamespaceVersion(name))
      list(name = name, version = version, raw_path = raw, path = observed$path, path_error = observed$path_error)
    })
    dlls <- lapply(getLoadedDLLs(), function(dll) {
      raw <- dll[["path"]]
      built_in <- identical(dll[["name"]], "base") && identical(raw, "base")
      observed <- if (built_in) list(path = "base", path_error = NULL) else observed_path(raw)
      list(name = dll[["name"]], raw_path = raw, path = observed$path, path_error = observed$path_error, built_in = built_in, dynamicLookup = dll[["dynamicLookup"]])
    })
    list(R_version = R.version.string, version = as.character(getRversion()), platform = R.version$platform, R_arch = .Platform$r_arch, dynlib_ext = .Platform$dynlib.ext, R_home = normalize(R.home()), library_paths = normalize(.libPaths()), namespaces = namespaces, DLLs = unname(dlls), session_info = info)
  }
  validate <- function(value) {
    stopifnot(identical(value$version, "4.6.0"), identical(value$R_arch, ""), identical(value$dynlib_ext, ".so"))
    stopifnot(identical(value$R_home, normalize(r_home)))
    stopifnot(setequal(value$library_paths, c(normalize(library), normalize(file.path(r_home, "library")))))
    for (item in list(c("disqover", "0.9.14"), c("RcppDE", "0.1.9"), c("jsonlite", "2.0.0"))) {
      actual <- Filter(function(row) identical(row$name, item[[1]]), value$namespaces)
      if (length(actual) != 1L || !identical(actual[[1]]$version, item[[2]])) stop(paste("Namespace version differs:", item[[1]]))
    }
    for (row in value$namespaces) {
      if (!is.null(row$path_error) || length(row$path) != 1L || !owned(row$path)) stop(paste("Namespace outside owned runtime:", row$name, "raw", row$raw_path, "normalized", row$path, "error", row$path_error))
    }
    for (row in value$DLLs) {
      if (row$built_in) {
        if (!identical(row$name, "base") || !identical(row$path, "base")) stop("Unknown built-in DLL sentinel")
      } else if (!is.null(row$path_error) || length(row$path) != 1L || !owned(row$path) || !(row$path %in% native_files)) {
        stop(paste("DLL outside declared native closure:", row$name, "raw", row$raw_path, "normalized", row$path, "error", row$path_error))
      }
    }
    invisible(TRUE)
  }
  before <- after <- NULL
  numerical_exit <- NULL
  numerical_error <- metadata_error <- NULL
  capture_validate <- function(label) {
    load_error <- NULL
    tryCatch({ for (item in c("jsonlite", "disqover", "RcppDE")) loadNamespace(item) }, error = function(e) load_error <<- conditionMessage(e))
    actual <- snapshot()
    # Retain the complete observation before any runtime/namespace/DLL admission check.
    if (identical(label, "before")) before <<- actual else after <<- actual
    if (!is.null(load_error)) stop(paste("Namespace load refused:", load_error))
    validate(actual)
  }
  tryCatch(capture_validate("before"), error = function(e) metadata_error <<- conditionMessage(e))
  if (is.null(metadata_error)) {
    if (!metadata_only) {
      numerical_exit <- 0L
      tryCatch(source(original, local = .GlobalEnv), error = function(e) { numerical_exit <<- 1L; numerical_error <<- list(message = conditionMessage(e), call = deparse(conditionCall(e))) })
    }
    tryCatch(capture_validate("after"), error = function(e) metadata_error <<- conditionMessage(e))
  }
  jsonlite::write_json(list(schema_version = "controlled-lra-R-process.v1", metadata_only = metadata_only, original_script = if (metadata_only) NULL else normalize(original), actual_trailing_arguments = commandArgs(trailingOnly = TRUE), numerical_exit = numerical_exit, numerical_error = numerical_error, metadata_exit = if (is.null(metadata_error)) 0L else 1L, metadata_error = metadata_error, before = before, after = after), destination, auto_unbox = TRUE, pretty = TRUE, null = "null", na = "null")
  if (!is.null(numerical_error)) stop(paste("Original numerical script failed:", numerical_error$message))
  if (!is.null(metadata_error)) stop(paste("Namespace metadata refused:", metadata_error))
  if (!metadata_only) stopifnot(identical(numerical_exit, 0L))
}
