sub func{
	$a = @_[0];
    while($a<5){
        $a += 1;
        print $a;
    }

sub func1{
  print "Hello";
}

func1();
}

#$a = 0;
func(0);

sub sum{
    $a = @_[0];
    $b = @_[1];
    $c = $a+$b;
    return $c;
}
$a=2;
$b=6;
$sum=sum($a,$b);
print $sum;