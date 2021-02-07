#!/usr/bin/perl -w
use strict;
use Getopt::Long;
###############################
###############################
my $usage = "Erreur!!  Usage: perl hahaha $!\n";
my $options = join(" ", @ARGV);

my ($query, $output, $map, $kof);


GetOptions ("query=s"               => \$query,
            "dir_out=s"              => \$output,
            ) or die("Error in command line arguments\n");
###########################################################
my @sample;
my %hash;
open(FILE, $query) or die "can't open $query";
while (<FILE>) {
    chomp;
    my @tab = split ("\t", $_);
    if ($tab[0] eq "ko"){
      for my $i (1..$#tab){
				#$tab[$i] =~ s/blastout\///;
        push (@sample, $tab[$i]);
      }
    }
    else{
      for my $i (1..$#tab){
        if ($tab[$i] > 0){
            $hash{$sample[$i-1]}{$tab[0]} = 1;
        }
      }
    }
}
close FILE;

for my $i (sort keys %hash){
  my $out = $output."/".$i.".ko_tableKEGG.txt";
  my $gene;
  open (W, ">$out") or die "can't open $out\n";
  for my $i2 (sort keys %{$hash{$i}}){
    $gene++;
    print W "gene$gene\t$i2\n";
  }
}
