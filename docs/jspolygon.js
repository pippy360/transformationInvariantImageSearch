    /*
     *  This is the Point constructor. Polygon uses this object, but it is
     *  just a really simple set of x and y coordinates.
     */
    function Point(px, py) {
    	this.x = px;
    	this.y = py;
    }

    /*
     *  This is the Polygon constructor. All points are center-relative.
     */
    function Polygon(c, clr) {

    	this.points = new Array();
    	this.center = c;
    	this.color = clr;  // used when drawing
    	
    }
    
    /*
     *  Point x and y values should be relative to the center.
     */
    Polygon.prototype.addPoint = function(p) {
    	this.points.push(p);
    }
    
    /*
     *  Point x and y values should be absolute coordinates.
     */
    Polygon.prototype.addAbsolutePoint = function(p) {
    	this.points.push( { "x": p.x - this.center.x, "y": p.y - this.center.y } );
    }

    /*
     * Returns the number of sides. Equal to the number of vertices.
     */
    Polygon.prototype.getNumberOfSides = function() {
    	return this.points.length;
    }
    
    /*
     * rotate the polygon by a number of radians
     */
    Polygon.prototype.rotate = function(rads) {
    	
    	for (var i = 0; i < this.points.length; i++) {
    		var x = this.points[i].x;
    		var y = this.points[i].y;
    		this.points[i].x = Math.cos(rads) * x - Math.sin(rads) * y;
    		this.points[i].y = Math.sin(rads) * x + Math.cos(rads) * y;
    	}
    	
    }
    
    /*
     *  The draw function takes as a parameter a Context object from
     *  a Canvas element and draws the polygon on it.
     */
    Polygon.prototype.draw = function(ctx) {

        ctx.save();

        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.moveTo(this.points[0].x + this.center.x, this.points[0].y + this.center.y);
        for (var i = 1; i < this.points.length; i++) {
        	ctx.lineTo(this.points[i].x + this.center.x, this.points[i].y + this.center.y);
        }
        ctx.closePath();
        ctx.fill();

        ctx.restore();
    	
    }

    /*
     *  This function returns true if the given point is inside the polygon,
     *  and false otherwise.
     */
    Polygon.prototype.containsPoint = function(pnt) {
    	
    	var nvert = this.points.length;
    	var testx = pnt.x;
    	var testy = pnt.y;
    	
    	var vertx = new Array();
    	for (var q = 0; q < this.points.length; q++) {
    		vertx.push(this.points[q].x + this.center.x);
    	}
    	
    	var verty = new Array();
    	for (var w = 0; w < this.points.length; w++) {
    		verty.push(this.points[w].y + this.center.y);
    	}

    	var i, j = 0;
    	var c = false;
    	for (i = 0, j = nvert - 1; i < nvert; j = i++) {
    		if ( ((verty[i]>testy) != (verty[j]>testy)) &&
    				(testx < (vertx[j]-vertx[i]) * (testy-verty[i]) / (verty[j]-verty[i]) + vertx[i]) )
    			c = !c;
    	}
    	return c;
    	
    }
    
    /*
     *  To detect intersection with another Polygon object, this
     *  function uses the Separating Axis Theorem. It returns false
     *  if there is no intersection, or an object if there is. The object
     *  contains 2 fields, overlap and axis. Moving the polygon by overlap
     *  on axis will get the polygons out of intersection.
     */
    Polygon.prototype.intersectsWith = function(other) {
    	
    	var axis = new Point();
    	var tmp, minA, maxA, minB, maxB;
    	var side, i;
    	var smallest = null;
    	var overlap = 99999999;

    	/* test polygon A's sides */
    	for (side = 0; side < this.getNumberOfSides(); side++)
    	{
    		/* get the axis that we will project onto */
    		if (side == 0)
    		{
    			axis.x = this.points[this.getNumberOfSides() - 1].y - this.points[0].y;
    			axis.y = this.points[0].x - this.points[this.getNumberOfSides() - 1].x;
    		}
    		else
    		{
    			axis.x = this.points[side - 1].y - this.points[side].y;
    			axis.y = this.points[side].x - this.points[side - 1].x;
    		}

    		/* normalize the axis */
    		tmp = Math.sqrt(axis.x * axis.x + axis.y * axis.y);
    		axis.x /= tmp;
    		axis.y /= tmp;

    		/* project polygon A onto axis to determine the min/max */
    		minA = maxA = this.points[0].x * axis.x + this.points[0].y * axis.y;
    		for (i = 1; i < this.getNumberOfSides(); i++)
    		{
    			tmp = this.points[i].x * axis.x + this.points[i].y * axis.y;
    			if (tmp > maxA)
    				maxA = tmp;
    			else if (tmp < minA)
    				minA = tmp;
    		}
    		/* correct for offset */
    		tmp = this.center.x * axis.x + this.center.y * axis.y;
    		minA += tmp;
    		maxA += tmp;

    		/* project polygon B onto axis to determine the min/max */
    		minB = maxB = other.points[0].x * axis.x + other.points[0].y * axis.y;
    		for (i = 1; i < other.getNumberOfSides(); i++)
    		{
    			tmp = other.points[i].x * axis.x + other.points[i].y * axis.y;
    			if (tmp > maxB)
    				maxB = tmp;
    			else if (tmp < minB)
    				minB = tmp;
    		}
    		/* correct for offset */
    		tmp = other.center.x * axis.x + other.center.y * axis.y;
    		minB += tmp;
    		maxB += tmp;

    		/* test if lines intersect, if not, return false */
    		if (maxA < minB || minA > maxB) {
    			return false;
    		} else {
    			var o = (maxA > maxB ? maxB - minA : maxA - minB);
    			if (o < overlap) {
    				overlap = o;
    			    smallest = {x: axis.x, y: axis.y};
    			}
    		}
    	}

    	/* test polygon B's sides */
    	for (side = 0; side < other.getNumberOfSides(); side++)
    	{
    		/* get the axis that we will project onto */
    		if (side == 0)
    		{
    			axis.x = other.points[other.getNumberOfSides() - 1].y - other.points[0].y;
    			axis.y = other.points[0].x - other.points[other.getNumberOfSides() - 1].x;
    		}
    		else
    		{
    			axis.x = other.points[side - 1].y - other.points[side].y;
    			axis.y = other.points[side].x - other.points[side - 1].x;
    		}

    		/* normalize the axis */
    		tmp = Math.sqrt(axis.x * axis.x + axis.y * axis.y);
    		axis.x /= tmp;
    		axis.y /= tmp;

    		/* project polygon A onto axis to determine the min/max */
    		minA = maxA = this.points[0].x * axis.x + this.points[0].y * axis.y;
    		for (i = 1; i < this.getNumberOfSides(); i++)
    		{
    			tmp = this.points[i].x * axis.x + this.points[i].y * axis.y;
    			if (tmp > maxA)
    				maxA = tmp;
    			else if (tmp < minA)
    				minA = tmp;
    		}
    		/* correct for offset */
    		tmp = this.center.x * axis.x + this.center.y * axis.y;
    		minA += tmp;
    		maxA += tmp;

    		/* project polygon B onto axis to determine the min/max */
    		minB = maxB = other.points[0].x * axis.x + other.points[0].y * axis.y;
    		for (i = 1; i < other.getNumberOfSides(); i++)
    		{
    			tmp = other.points[i].x * axis.x + other.points[i].y * axis.y;
    			if (tmp > maxB)
    				maxB = tmp;
    			else if (tmp < minB)
    				minB = tmp;
    		}
    		/* correct for offset */
    		tmp = other.center.x * axis.x + other.center.y * axis.y;
    		minB += tmp;
    		maxB += tmp;

    		/* test if lines intersect, if not, return false */
    		if (maxA < minB || minA > maxB) {
    			return false;
    		} else {
    			var o = (maxA > maxB ? maxB - minA : maxA - minB);
    			if (o < overlap) {
    				overlap = o;
    			    smallest = {x: axis.x, y: axis.y};
    			}
    		}
    	}

    	return {"overlap": overlap + 0.001, "axis": smallest};
    	
    }
