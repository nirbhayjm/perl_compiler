$wflg=0;
$tflg=0;
$dflg=0;
$c=2;
switch($c)
{
case (1){ print 5;}
case (2){ $wflg = 1; print 2;last;print 3;}
case (3){}
case (4){$tflg = 1; last;}
case (5)
            {$dflg = 1;
            last;}

}
