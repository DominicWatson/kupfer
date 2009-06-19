#! /usr/bin/env python
# encoding: utf-8

import os
import sys
import Configure
import Utils

# the following two variables are used by the target "waf dist"
APPNAME="kupfer"
VERSION = "undefined"

def _get_git_version():
	""" try grab the current version number from git"""
	version = None
	if os.path.exists(".git"):
		try:
			version = os.popen("git describe").read().strip()
		except Exception, e:
			print e
	return version

def _read_git_version():
	"""Read version from git repo, or from GIT_VERSION"""
	version = _get_git_version()
	if not version and os.path.exists("GIT_VERSION"):
		f = open("GIT_VERSION", "r")
		version = f.read().strip()
		f.close()
	if version:
		global VERSION
		VERSION = version

_read_git_version()

VERSION_MAJOR_MINOR = ".".join(VERSION.split(".")[0:2])

# these variables are mandatory ('/' are converted automatically)
srcdir = '.'
blddir = 'build'

def dist():
	"""Make the dist tarball and print its SHA-1 """
	def write_git_version():
		""" Write the revision to a file called GIT_VERSION,
		to grab the current version number from git when
		generating the dist tarball."""
		version = _get_git_version()
		if not version:
			return False
		version_file = open("GIT_VERSION", "w")
		version_file.write(version + "\n")
		version_file.close()
		return True

	import Scripting
	write_git_version()
	Scripting.g_gz = "gz"
	Scripting.dist(APPNAME, VERSION)

def set_options(opt):
	# options for disabling pyc or pyo compilation
	opt.tool_options("python")
	opt.tool_options("misc")
	opt.tool_options("gnu_dirs")

def configure(conf):
	conf.check_tool("python")
	conf.check_python_version((2,5,0))
	conf.check_tool("misc gnu_dirs")
	try:
		# BUG: intltool requires gcc
		conf.check_tool("gcc intltool")
	except Configure.ConfigurationError, e:
		print "Disabling localization (%s)" % e

	python_modules = """
		gio
		gtk
		xdg
		dbus
		"""
	for module in python_modules.split():
		conf.check_python_module(module)

	conf.find_program("dbus-send")

	# no "optimized" bytecode
	conf.env["PYO"] = 0
	conf.env["KUPFER"] = Utils.subst_vars("${BINDIR}/kupfer", conf.env)
	conf.env["VERSION"] = VERSION

	print "Installing to PYTHONPATH: %s" % conf.env["PYTHONDIR"]

def new_module(bld, name, sources=None):
	if not sources: sources = name
	obj = bld.new_task_gen("py")
	obj.find_sources_in_dirs(sources)
	obj.install_path = "${PYTHONDIR}/%s" % name
	return obj

def build(bld):
	# kupfer module version info file
	version_subst_file = "kupfer/version_subst.py"
	obj = bld.new_task_gen("subst",
		source=version_subst_file + ".in",
		target=version_subst_file,
		install_path="${PYTHONDIR}/kupfer",
		dict = bld.env,
		)

	# modules
	new_module(bld, "kupfer")
	new_module(bld, "kupfer/plugin")
	# binary
	bld.install_as("${BINDIR}/kupfer", "kupfer-activate.sh", chmod=0755)

	# Install .desktop file
	# Specially preparated to setup
	# PYTHONPATH with /usr/bin/env
	# and the absolute path to the kupfer binary
	desktop_subst_file = "kupfer.desktop"
	dtp = bld.new_task_gen("subst",
		source = desktop_subst_file + ".in",
		target = desktop_subst_file,
		install_path = "${DATADIR}/applications",
		chmod = 0755,
		dict = bld.env,
		)

	# Add localization if available
	if bld.env['INTLTOOL']:
		bld.add_subdirs("po")

def poextract(util):
	"""Extract new strings for localization"""
	for line in open("po/LINGUAS"):
		""" Run xgettext for all listed languages
		to extract translatable strings and merge with
		the old file """
		if line.startswith("#"):
			continue
		lang = line.strip()

		lang_file = "po/%s.po" % lang
		print "Writing", lang_file
		if os.path.exists(lang_file):
			# Run twice to refresh all file:line comments
			os.popen("xgettext -f po/POTFILES.in --output=%s -j --omit-header --no-location" % lang_file)
			os.popen("xgettext -f po/POTFILES.in --output=%s -F -j --omit-header" % lang_file)
		else:
			os.popen("xgettext -f po/POTFILES.in --output=%s -F" % lang_file)

def shutdown():
	pass


