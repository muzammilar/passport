# -*- coding: utf-8 -*-
"""

    ppcore.ppbox
    ~~~~~~~~~~~~~~

    This module is used to create a single geodisic box for Passport.

    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from shapely.geometry import box
from geopy.distance import great_circle as great_circle_distance


class Box():
    """

        A class to store information about the maz possible distance travelled by each ping/trace measurement

        x1 is the longitude of bottom left point
        x2 is the longitude of the top right point
        y1 is the latitude of bottom left point
        y2 is the latitude of the top right point

        ------------  <-----(x2, y2)
        |          |
        |          |
        |          |
        |          |
        ------------

        ^
        |
        ---- (x1, y1)
        Things will go south if you pass args in the wrong order

        :box: the shapely box representing the primary shape
        :second_box: the shapely box representing the box that is created (when we convert cylender
            shape to a rectangle) i.e. cases where international date line is crossed
    """

    def __init__(self, x1=0, y1=0, x2=1, y2=1):
        """

        :param x1: longitude of bottom left point
        :param y1: latitude of bottom left point
        :param x2: longitude of the top right point
        :param y2: latitude of the top right point
        """
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

        try:
            self.box = box(x1, y1, x2, y2)
            self.box_second = None
        except:
            self.box = None

        if self.x1 > self.x2:
            # add a simple 180.
            self.box = box(x1, y1, x2 + 360, y2)
            self.box_second = box(x1 - 360, y1, x2, y2)

    def area(self):
        """ Returns the area of the box (in terms of lat-lon)"""
        y_max = self.y2 
        if self.y2 < self.y1:
            y_max += 360
        return (y_max - self.y1) * (self.x2 - self.x1)

    def center(self):
        """ The middle point of a box"""
        center_point = self.box.centroid
        if center_point.x > 180:
            center_point_x = center_point.x - 360
            return center_point_x, center_point.y
        return center_point.x, center_point.y

    def from_box(self, current_box):
        """Creates a `SINGLE` box from another box, the corrects the boundary points of the box"""
        cbb = current_box.bounds
        self.x1, self.y1, self.x2, self.y2 = cbb[0], cbb[1], cbb[2], cbb[3]
        self.box = current_box
        # if long was larger than 180. decrement 360.
        if self.x2 > 180:
            self.x2 -= 360
        if self.x1 < -180:
            self.x1 += 360

    def __lt__(self, other): # use in the sorting
        return self.area() < other.area()


def intersect_boxes(boxes):
    """
    Performs intersection on the SoL Boxes created by each individual ping measurement

    :param boxes: A list containing instances of <Box>. [<Box> 1, <Box> 2, ...]
    :return: An instance of <Box> that has the intersection of all the above ones, or the shortest ones
    """

    # get intersections
    current_box = boxes[0].box

    for box_object in boxes[1:]:
        # intersect current_box with the next in array
        if current_box is not None:
            new_current_box = current_box.intersection(box_object.box)
            if new_current_box.area == 0:
                # check the second box
                if box_object.box_second is not None:
                    new_current_box = current_box.intersection(box_object.box_second)
                    if new_current_box.area == 0:
                        current_box = None
                    else:
                        current_box = new_current_box        
                else:
                    current_box = None                    

    if current_box is not None:
        ret_box = Box()
        ret_box.from_box(current_box)
        current_box = ret_box

    return current_box


def intersect_boxes_second(boxes):
    """
    Performs intersection on the SoL Boxes created by each individual ping measurement. Thif function intersects
    secondary boxes.

    :param boxes: A list containing instances of <Box>. [<Box> 1, <Box> 2, ...]
    :return: An instance of <Box> that has the intersection of all the above ones, or the shortest ones
    """

    # get intersections
    current_box = boxes[0].box
    prev_current_box = current_box
    for box_object in boxes[1:]:
        # intersect current_box with the next in array
        if current_box is not None:
            prev_current_box = current_box
            new_current_box = current_box.intersection(box_object.box)
            if new_current_box.area == 0:
                # check the second box
                if box_object.box_second is not None:
                    new_current_box = current_box.intersection(box_object.box_second)
                    if new_current_box.area == 0:
                        current_box = None
                    else:
                        current_box = new_current_box        
                else:
                    current_box = None         

    if current_box is not None:
        ret_box = Box()
        ret_box.from_box(current_box)
        current_box = ret_box
    else:
        ret_box = Box()
        ret_box.from_box(prev_current_box)
        current_box = ret_box

    return current_box


def total_area(lat_bottom_left, lon_bottom_left, lat_top_right, lon_top_right):
    """
    Returns the total area of the region. Please note that this only works for small areas and regions
    close to eqautor.

    :param lat_bottom_left: float (-90 to 90)
    :param lon_bottom_left: float (-180 to 180)
    :param lat_top_right: float  (-90 to 90)
    :param lon_top_right: float (-180 to 180)

    :return: area in km^2

    # muz: there might be a minor bug in my code here.
    # Note: great_circle_distance takes two tuples each of (lat, lon) i.e (y,x) not
    # (x,y) i.e (lon, lat)

    """
    # correct case for date line by simply adding 360
    corrected_lon_top_right = lon_top_right
    if lon_bottom_left > lon_top_right:
        corrected_lon_top_right = lon_top_right + 360

    # in order to ovoid shortest distance. if their dist > 180
    # this is because geopy always go for a shortest distace

    # horizontal distance
    dist_x = 0
    dist_y = 0
    pt1 = (lat_bottom_left, lon_bottom_left)
    if corrected_lon_top_right - lon_bottom_left > 180:
        mid_lon = corrected_lon_top_right + lon_bottom_left
        mid_lon = mid_lon / 2.0
        pt2 = (lat_bottom_left, mid_lon)
        pt3 = (lat_bottom_left, corrected_lon_top_right)
        dist_x += great_circle_distance(pt1, pt2).kilometers
        dist_x += great_circle_distance(pt2, pt3).kilometers
    else:
        pt2 = (lat_bottom_left, corrected_lon_top_right)
        dist_x += great_circle_distance(pt1, pt2).kilometers

    # vertical distance
    if lat_top_right - lat_bottom_left > 90:
        mid_lat = lat_top_right + lat_bottom_left
        mid_lat = mid_lat / 2.0
        pt2 = (mid_lat, lon_bottom_left)
        pt3 = (lat_top_right, lon_bottom_left)
        dist_y += great_circle_distance(pt1, pt2).kilometers
        dist_y += great_circle_distance(pt2, pt3).kilometers
    else:
        pt2 = (lat_top_right, lon_bottom_left)
        dist_y += great_circle_distance(pt1, pt2).kilometers

    area = dist_x * dist_y
    return area
