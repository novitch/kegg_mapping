#!/usr/bin/perl -w
use strict;
use Getopt::Long;
###############################
# CONCATENATION OF centrifuge_report
# perl concat.pl -query=[listof sample files] -output=[normalized data output] -out_spe=[normalized species data output] -out_raw=[unique raw count data output] -out_rawsp=[unique raw count species data output]
###############################
my $usage = "Erreur!!  Usage: perl hahaha $!\n";
my $options = join(" ", @ARGV);

my ($query, $output, $map, $kof);


GetOptions ("query=s"               => \$query,
            "output=s"              => \$output,
            ) or die("Error in command line arguments\n");
###########################################################
my @sample;
my %hash;
open(FILE, $query) or die "can't open $query";
while (<FILE>) {
    chomp;
    my $genome;
    if (($_ =~ /.*\/(.*).ko_tableKEGG_modules.tsv/) || ($_ =~ /(.*).ko_tableKEGG_modules.tsv/)|| ($_ =~ /(.*)_modules.tsv/)){
      $genome= $1;
      push (@sample, $genome);
      open (FILE1, $_) or die "can't open $_";
      while (<FILE1>) {
          chomp;
          my @tab=split("\t", $_);
          my $val;
          if ($tab[1]eq "0"){
            $val = "4";
          }
          elsif ($tab[1]eq "1"){
            $val = "3";
          }
		  elsif ($tab[1]eq "2"){
			$val = "2";
		  }
          elsif ($tab[1]eq "3"){
            $val = "1";
          }
          elsif ($tab[1]eq "4"){
            $val = "0";
          }
          $hash{$tab[0]}{$genome}=$val;
      }
    }
}
open(W, ">$output") or die "pbm output $usage";
print W "module"."\t".join("\t", @sample)."\n";
for my $i (sort keys %hash){
  print W $i;
  for my $i2 (0..$#sample){
    if ($hash{$i}{$sample[$i2]}){
      print W "\t".$hash{$i}{$sample[$i2]};
    }
    else{
      print W "\t0";
    }
  }
  print W "\n";
}
