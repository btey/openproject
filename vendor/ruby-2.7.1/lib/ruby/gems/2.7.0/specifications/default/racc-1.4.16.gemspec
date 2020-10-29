# -*- encoding: utf-8 -*-
# stub: racc 1.4.16 ruby lib
# stub: ext/racc/extconf.rb

Gem::Specification.new do |s|
  s.name = "racc".freeze
  s.version = "1.4.16"

  s.required_rubygems_version = Gem::Requirement.new(">= 0".freeze) if s.respond_to? :required_rubygems_version=
  s.require_paths = ["lib".freeze]
  s.authors = ["Minero Aoki".freeze, "Aaron Patterson".freeze]
  s.date = "2020-04-16"
  s.description = "Racc is a LALR(1) parser generator.\n  It is written in Ruby itself, and generates Ruby program.\n\n  NOTE: Ruby 1.8.x comes with Racc runtime module.  You\n  can run your parsers generated by racc 1.4.x out of the\n  box.\n".freeze
  s.email = [nil, "aaron@tenderlovemaking.com".freeze]
  s.executables = ["racc".freeze, "racc2y".freeze, "y2racc".freeze]
  s.extensions = ["ext/racc/extconf.rb".freeze]
  s.extra_rdoc_files = ["Manifest.txt".freeze, "README.ja.rdoc".freeze, "README.rdoc".freeze, "rdoc/en/NEWS.en.rdoc".freeze, "rdoc/en/grammar.en.rdoc".freeze, "rdoc/ja/NEWS.ja.rdoc".freeze, "rdoc/ja/debug.ja.rdoc".freeze, "rdoc/ja/grammar.ja.rdoc".freeze, "rdoc/ja/parser.ja.rdoc".freeze, "README.ja.rdoc".freeze, "README.rdoc".freeze]
  s.files = ["Manifest.txt".freeze, "README.ja.rdoc".freeze, "README.rdoc".freeze, "bin/racc".freeze, "bin/racc2y".freeze, "bin/y2racc".freeze, "ext/racc/extconf.rb".freeze, "racc.rb".freeze, "racc/compat.rb".freeze, "racc/debugflags.rb".freeze, "racc/exception.rb".freeze, "racc/grammar.rb".freeze, "racc/grammarfileparser.rb".freeze, "racc/info.rb".freeze, "racc/iset.rb".freeze, "racc/logfilegenerator.rb".freeze, "racc/parser-text.rb".freeze, "racc/parser.rb".freeze, "racc/parserfilegenerator.rb".freeze, "racc/sourcetext.rb".freeze, "racc/state.rb".freeze, "racc/statetransitiontable.rb".freeze, "racc/static.rb".freeze, "rdoc/en/NEWS.en.rdoc".freeze, "rdoc/en/grammar.en.rdoc".freeze, "rdoc/ja/NEWS.ja.rdoc".freeze, "rdoc/ja/debug.ja.rdoc".freeze, "rdoc/ja/grammar.ja.rdoc".freeze, "rdoc/ja/parser.ja.rdoc".freeze]
  s.homepage = "http://i.loveruby.net/en/projects/racc/".freeze
  s.licenses = ["MIT".freeze]
  s.rdoc_options = ["--main".freeze, "README.rdoc".freeze]
  s.rubygems_version = "3.1.2".freeze
  s.summary = "Racc is a LALR(1) parser generator".freeze

  if s.respond_to? :specification_version then
    s.specification_version = 4
  end

  if s.respond_to? :add_runtime_dependency then
    s.add_development_dependency(%q<rake-compiler>.freeze, [">= 0.4.1"])
    s.add_development_dependency(%q<minitest>.freeze, ["~> 4.7"])
    s.add_development_dependency(%q<rdoc>.freeze, [">= 4.0", "< 7"])
    s.add_development_dependency(%q<hoe>.freeze, ["~> 3.18"])
  else
    s.add_dependency(%q<rake-compiler>.freeze, [">= 0.4.1"])
    s.add_dependency(%q<minitest>.freeze, ["~> 4.7"])
    s.add_dependency(%q<rdoc>.freeze, [">= 4.0", "< 7"])
    s.add_dependency(%q<hoe>.freeze, ["~> 3.18"])
  end
end